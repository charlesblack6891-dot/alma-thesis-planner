"""Topic-based project lookup (Stage 10 input).

Lets a caller skip knowing a specific ALMA project code, PI, and target up
front: give a sentence or two describing a research interest, and this picks
a matching already-vetted project.

Reuses the sibling `alma_thesis_planning` checkout (ptorrey's `almathesis`
package) as the candidate pool -- its `queue.csv` (pre-vetted publication
verdicts) and `projects/<code>/` ingest output (`metadata.json` +
`input_files/data_description.md`) -- rather than re-implementing ALMA
archive ingest here. Candidates are restricted to rows already fully checked
(status "done" or "published") AND already ingested locally, so this makes
zero archive or ADS network calls of its own. Which verdicts count as a match
is controlled by `list_candidates`'s `publication_filter` -- "unpublished"
(the default, and the safest choice for a genuinely new thesis project),
"published" (published or partially published), or "both".
"""
from __future__ import annotations

import csv
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from blocks import extract_block
from llm import call_claude
from state import DESCRIPTION_FILE

SOURCE_REPO_ENV = "ALMA_QUEUE_REPO"

# Which queue.csv `verdict` values count as a match for each publication_filter
# choice. "published" also pulls in "partially published" -- a row that's
# still worth surfacing under a "published" filter rather than splitting into
# a fourth bucket nobody would meaningfully choose separately.
_VERDICTS_BY_PUBLICATION_FILTER: dict[str, set[str]] = {
    "unpublished": {"unpublished"},
    "published": {"published", "partially published"},
    "both": {"unpublished", "published", "partially published"},
}


def default_source_repo() -> Path:
    """Sibling `alma_thesis_planning` checkout, overridable via $ALMA_QUEUE_REPO."""
    override = os.environ.get(SOURCE_REPO_ENV)
    if override:
        return Path(override)
    return Path(__file__).resolve().parent.parent / "alma_thesis_planning-ptorrey"


@dataclass
class Candidate:
    project_code: str
    title: str
    # Pulled from metadata.json (free -- local files, no API cost) so the
    # matching prompt has real scientific signal to judge relevance against,
    # not just a title. Defaulted for tests/callers that only care about
    # project_code/title.
    scientific_categories: list[str] = field(default_factory=list)
    science_keywords: list[str] = field(default_factory=list)
    proposal_abstract: str = ""


def list_candidates(source_repo: Path, publication_filter: str = "unpublished") -> list[Candidate]:
    """Already-ingested candidates from `source_repo`'s queue.csv, restricted
    to a chosen publication status.

    `publication_filter` is one of "unpublished" (default -- the safest
    choice for a genuinely new thesis project), "published" (published or
    partially published), or "both" (no verdict restriction). Either way, a
    queue row qualifies only if it's been fully checked (status "done" or
    "published" -- this skips pending/failed rows) AND the project has
    actually been ingested on disk -- a `pending` row has a title in some
    queue snapshots but no `data_description.md` yet, so status/verdict alone
    isn't enough to guarantee the files this needs exist.
    """
    if publication_filter not in _VERDICTS_BY_PUBLICATION_FILTER:
        raise ValueError(
            f"Unknown publication_filter {publication_filter!r} -- expected one of "
            f"{sorted(_VERDICTS_BY_PUBLICATION_FILTER)}"
        )
    wanted_verdicts = _VERDICTS_BY_PUBLICATION_FILTER[publication_filter]

    queue_path = source_repo / "queue.csv"
    if not queue_path.exists():
        raise FileNotFoundError(
            f"queue.csv not found at {queue_path} -- set ${SOURCE_REPO_ENV} to point "
            "at a checkout of ptorrey/alma_thesis_planning"
        )

    candidates = []
    with queue_path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row.get("status") not in ("done", "published") or row.get("verdict") not in wanted_verdicts:
                continue
            code = row["project_code"]
            desc_path = source_repo / "projects" / code / "input_files" / DESCRIPTION_FILE
            meta_path = source_repo / "projects" / code / "metadata.json"
            if not (desc_path.exists() and meta_path.exists()):
                continue
            metadata = json.loads(meta_path.read_text(encoding="utf-8"))
            candidates.append(Candidate(
                project_code=code,
                title=row.get("title", ""),
                scientific_categories=metadata.get("scientific_categories", []),
                science_keywords=metadata.get("science_keywords", []),
                proposal_abstract=metadata.get("proposal_abstract", ""),
            ))
    return candidates


def load_project_data(source_repo: Path, project_code: str) -> dict:
    """Read a candidate's PI, target(s), and data description off disk.

    `pi` and `target` are derived from the ingest-stage `metadata.json`
    (`pi_name`, and the deduplicated `target_name`s across `mous_records`) so
    they line up with what a from-scratch `run_pipeline.py` invocation would
    be given by hand.
    """
    project_dir = source_repo / "projects" / project_code
    metadata = json.loads((project_dir / "metadata.json").read_text(encoding="utf-8"))
    data_description = (project_dir / "input_files" / DESCRIPTION_FILE).read_text(encoding="utf-8")

    targets: list[str] = []
    for record in metadata.get("mous_records", []):
        name = record.get("target_name")
        if name and name not in targets:
            targets.append(name)

    return {
        "project_code": project_code,
        "pi": metadata.get("pi_name") or "Unknown",
        "target": ", ".join(targets) if targets else "Unknown",
        "data_description": data_description,
        "title": metadata.get("title", ""),
    }


_ABSTRACT_EXCERPT_CHARS = 350


def _candidate_block(c: Candidate) -> str:
    lines = [f"- {c.project_code}: {c.title}"]
    if c.scientific_categories:
        lines.append(f"  Scientific categories: {', '.join(c.scientific_categories)}")
    if c.science_keywords:
        lines.append(f"  Science keywords: {', '.join(c.science_keywords)}")
    if c.proposal_abstract:
        excerpt = c.proposal_abstract[:_ABSTRACT_EXCERPT_CHARS]
        if len(c.proposal_abstract) > _ABSTRACT_EXCERPT_CHARS:
            excerpt += "..."
        lines.append(f"  Proposal abstract (excerpt): {excerpt}")
    return "\n".join(lines)


def available_categories_and_keywords(candidates: list[Candidate]) -> tuple[list[str], dict[str, list[str]]]:
    """Distinct scientific categories present in the local candidate pool,
    and for each category the distinct science keywords that co-occur with
    it on at least one candidate.

    Built from whatever's already ingested locally, not the full official
    ALMA controlled vocabulary -- every (category, keyword) pair this
    returns is guaranteed to match at least one real candidate, so a
    category-then-keyword dropdown pair driven by this never offers a
    combination that leads nowhere.
    """
    categories: set[str] = set()
    keywords_by_category: dict[str, set[str]] = {}
    for c in candidates:
        for cat in c.scientific_categories:
            categories.add(cat)
            keywords_by_category.setdefault(cat, set()).update(c.science_keywords)
    return sorted(categories), {cat: sorted(kws) for cat, kws in keywords_by_category.items()}


def filter_by_category_keyword(candidates: list[Candidate], category: str, keyword: str) -> list[Candidate]:
    """Candidates whose scientific categories/science keywords both include
    the given values -- the hard filter that lets a category+keyword pick
    focus the search instead of matching on free text alone."""
    return [c for c in candidates if category in c.scientific_categories and keyword in c.science_keywords]


def pick_project_prompt(topic: str, candidates: list[Candidate]) -> str:
    listing = "\n".join(_candidate_block(c) for c in candidates)
    topic_section = (
        topic.strip()
        if topic.strip()
        else "(no free-text prompt given -- these candidates were already filtered down by the "
             "student's chosen scientific category and science keyword; pick whichever one is the "
             "strongest overall match to that category/keyword pair.)"
    )
    return f"""A student described their research interest. Your job is to find the single ALMA project from the candidate list below that is a genuine scientific match to that interest -- not merely the least-unrelated option.

Student's interest:
{topic_section}

Candidates (project code, title, scientific categories, science keywords, and a proposal abstract excerpt where available):
{listing}

Matching rubric -- apply strictly:
- A genuine match means the candidate's title, science keywords, or abstract are actually about the phenomenon, object type, or physical process the student named (e.g. if they said "supernovae," the candidate must be about supernovae or their remnants, not just something else "energetic" or "extreme"). Superficial or thematic-sounding overlap (both are "exotic," both involve "extreme physics," both are "interesting transients") does NOT count as a match.
- Do not force a pick just because the list is short or because one candidate is the closest of a bad set. If every candidate is actually about a different phenomenon than what the student asked for, the correct answer is that there is no match -- say so, do not pick the least-wrong one and present it as a fit.
- Grade your own pick's quality honestly: GOOD only if the core phenomenon/object type genuinely lines up; WEAK if there's a real but partial/tangential connection worth flagging to the student before they commit; NONE if nothing in the list is a genuine match.

Respond in the following format:

\\begin{{PICK}}
PROJECT_CODE: <project_code copied exactly as written above, or NONE>
MATCH_QUALITY: GOOD or WEAK or NONE
REASON: <one or two sentences a student could use to sanity-check this pick before spending time/tokens on it -- name the specific phenomenon/keyword overlap (or lack of it), not a generic restatement>
\\end{{PICK}}

If MATCH_QUALITY is NONE, PROJECT_CODE must also be NONE."""


@dataclass
class Pick:
    candidate: Candidate
    match_quality: str  # "GOOD" or "WEAK"
    reason: str


def pick_project(
    topic: str,
    candidates: list[Candidate],
    *,
    call_claude_fn: Callable[[str], str] = call_claude,
) -> Pick:
    """Match `topic` against `candidates` and return the best genuine match.

    Unlike a bare best-of-N pick, this can come back empty-handed: if the
    model judges that no candidate is a real scientific match to the topic
    (rather than just the closest of an unrelated set), it raises a ValueError
    naming that explicitly, instead of silently returning an unrelated project
    dressed up as a match -- confirmed live to happen otherwise (a "super
    luminous supernovae" topic matched to an unrelated protostellar-outflow
    survey purely because the pool had no supernova candidate).

    `call_claude_fn` is injectable (Stage 3/5's pattern) so the matching
    logic can be unit tested with zero live calls.
    """
    if not candidates:
        raise ValueError("no unpublished, already-ingested candidates available to pick from")

    raw = call_claude_fn(pick_project_prompt(topic, candidates))
    block = extract_block(raw, "PICK", repair_fn=call_claude_fn)

    picked_code = None
    match_quality = None
    reason_parts: list[str] = []
    for line in block.splitlines():
        stripped = line.strip()
        upper = stripped.upper()
        if upper.startswith("PROJECT_CODE:"):
            picked_code = stripped.split(":", 1)[1].strip()
        elif upper.startswith("MATCH_QUALITY:"):
            match_quality = stripped.split(":", 1)[1].strip().upper()
        elif upper.startswith("REASON:"):
            reason_parts.append(stripped.split(":", 1)[1].strip())
    reason = " ".join(reason_parts) or "(no reason given)"

    if picked_code is None or match_quality is None:
        raise ValueError(f"Could not parse a PROJECT_CODE/MATCH_QUALITY pair from the model's response:\n{block}")

    if match_quality == "NONE" or picked_code.upper() == "NONE":
        raise ValueError(
            f"No candidate in the local pool of {len(candidates)} already-vetted, already-unpublished "
            f"ALMA projects is a genuine scientific match for \"{topic}\" -- {reason} Try manual mode "
            "with a dataset you already know about, or a broader/different topic."
        )

    by_code = {c.project_code: c for c in candidates}
    if picked_code not in by_code:
        raise ValueError(
            f"Claude picked {picked_code!r}, which is not among the {len(candidates)} candidates"
        )
    return Pick(candidate=by_code[picked_code], match_quality=match_quality, reason=reason)
