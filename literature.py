"""Published/novelty check (Stage 6).

Combines a plain (non-LLM) Semantic Scholar REST search with a Claude call
reframed around the dataset's own project code/PI/target -- ported from
Denario's novelty_prompt/summary_literature_prompt -- no LangChain, no API
keys for the Claude side. Per Stage 2's finding, the prompt always hands
Claude real search evidence and asks it to determine the verdict; it never
asks for a predetermined answer (a canned-verdict test prompt got an outright
refusal as prompt-injection-like during Stage 2's stress test).
"""
from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Callable

from blocks import extract_block
from llm import call_claude

SEMANTIC_SCHOLAR_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
SEMANTIC_SCHOLAR_FIELDS = "title,abstract,year,authors,externalIds,url"

# On this machine, AVG Antivirus's Web/Mail Shield intercepts HTTPS with its own
# self-signed root cert. Python 3.13's ssl module enforces VERIFY_X509_STRICT by
# default, which rejects that cert (its Basic Constraints extension isn't marked
# critical, an RFC 5280 violation) even once it's trusted -- so beyond adding the
# cert to the trust store, the strict flag itself has to be relaxed for this
# connection. Loaded lazily/defensively: harmless if the cert file doesn't exist
# (e.g. a different machine, or AVG not installed).
_AVG_INTERCEPT_CERT = r"C:\ProgramData\AVG\Antivirus\wscert.pem"


def _ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    try:
        ctx.load_verify_locations(cafile=_AVG_INTERCEPT_CERT)
    except (FileNotFoundError, ssl.SSLError):
        pass
    if hasattr(ssl, "VERIFY_X509_STRICT"):
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    return ctx


@dataclass
class PaperHit:
    title: str
    year: int | None
    authors: list[str]
    abstract: str | None
    url: str | None


def search_semantic_scholar(
    query: str, *, limit: int = 10, timeout: float = 20, max_retries: int = 3
) -> list[PaperHit]:
    """Plain REST call to the Semantic Scholar Graph API -- no LLM involved.

    Retries with exponential backoff on HTTP 429 (the unauthenticated tier's
    shared rate limit is easy to hit). Returns an empty list (rather than
    raising) if all retries are exhausted or another failure occurs, since
    this is a best-effort evidence source, not a hard dependency -- callers
    should treat an empty list as "no evidence found", not "definitely
    unpublished".
    """
    params = urllib.parse.urlencode({"query": query, "limit": limit, "fields": SEMANTIC_SCHOLAR_FIELDS})
    url = f"{SEMANTIC_SCHOLAR_SEARCH_URL}?{params}"
    ctx = _ssl_context()

    data = None
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(url, timeout=timeout, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < max_retries - 1:
                time.sleep(2**attempt)
                continue
            return []
        except Exception:
            return []
    if data is None:
        return []

    hits = []
    for paper in data.get("data", []) or []:
        authors = [a.get("name", "") for a in (paper.get("authors") or [])]
        hits.append(
            PaperHit(
                title=paper.get("title") or "",
                year=paper.get("year"),
                authors=authors,
                abstract=paper.get("abstract"),
                url=paper.get("url"),
            )
        )
    return hits


def _format_hits(hits: list[PaperHit]) -> str:
    if not hits:
        return "(no results found)"
    lines = []
    for i, hit in enumerate(hits, 1):
        authors = ", ".join(hit.authors) if hit.authors else "unknown authors"
        abstract = (hit.abstract or "(no abstract)")[:500]
        lines.append(
            f'{i}. "{hit.title}" ({hit.year}) -- {authors}\n'
            f"   URL: {hit.url or 'n/a'}\n"
            f"   Abstract: {abstract}"
        )
    return "\n".join(lines)


def novelty_prompt(
    project_code: str,
    pi: str,
    target: str,
    data_description: str,
    search_results: list[PaperHit],
) -> str:
    return f"""You are checking whether a specific ALMA observing project's data has already been used in a published, peer-reviewed paper. You are given the project's own description and a set of real search results from Semantic Scholar for related terms. Determine the verdict from this evidence -- do not assume a predetermined answer either way.

Be careful: a paper about the same astronomical target, or by an overlapping author, does NOT by itself mean this specific project's data was used -- the same target can have multiple independent ALMA datasets and publications. Only count a match as PUBLISHED if a search result plausibly analyzes data consistent with this project's specific description (the stated project code if it appears, the specific science goal/methods/wavelength described, and consistent author overlap) -- not just a shared target or a shared author.

Self-citation rule (apply this consistently, it is a common case): if the project description itself explicitly and specifically names a publication that reports analysis of THIS project's data -- e.g. it gives a DOI, journal/arXiv reference, or author list, and ties it to this project's specific code/target/method rather than just mentioning the target in passing -- treat that as sufficient evidence for PUBLISHED on its own. Do NOT downgrade to NOT_PUBLISHED or UNKNOWN merely because Semantic Scholar returned zero corroborating results; Semantic Scholar's index lags recent publications and a specific, well-formed self-citation is stronger evidence than an empty search. Only discount the description's own citation if the search results (or the description itself) affirmatively contradict it -- e.g. the cited work turns out to be about a different dataset, or the description's citation is vague/unverifiable (no DOI, no specific journal, just "this has probably been studied before"). A vague, non-specific mention should NOT be treated as sufficient on its own; a specific, well-formed one should.

ALMA project code: {project_code}
PI: {pi}
Target: {target}

Project description:
{data_description}

Semantic Scholar search results:
{_format_hits(search_results)}

Respond in the following format:

\\begin{{LITERATURE}}
VERDICT: PUBLISHED or NOT_PUBLISHED
JUSTIFICATION: <1-3 sentences explaining the verdict, referencing which search result(s) it's based on, or why none of the results are a match>
CITATIONS:
<numbered list of the most relevant results as background reading -- title/authors/year/url; write "(none directly relevant)" if none qualify>
\\end{{LITERATURE}}"""


@dataclass
class LiteratureResult:
    verdict: str  # "PUBLISHED", "NOT_PUBLISHED", or "UNKNOWN" if unparseable
    raw: str  # full \begin{LITERATURE}...\end{LITERATURE} block, always preserved


def check_published(
    project_code: str,
    pi: str,
    target: str,
    data_description: str,
    *,
    search_fn: Callable[[str], list[PaperHit]] = lambda q: search_semantic_scholar(q),
    call_claude_fn: Callable[[str], str] = call_claude,
) -> LiteratureResult:
    """Run the published/novelty check for one ALMA project.

    `search_fn`/`call_claude_fn` are injectable (Stage 3/5's pattern) so this
    can be unit tested with zero live network or `claude` calls.
    """
    query = f"{target} ALMA {pi}"
    hits = search_fn(query)
    prompt = novelty_prompt(project_code, pi, target, data_description, hits)
    raw = call_claude_fn(prompt)
    block = extract_block(raw, "LITERATURE", repair_fn=call_claude_fn)

    verdict = "UNKNOWN"
    for line in block.splitlines():
        stripped = line.strip().upper()
        if stripped.startswith("VERDICT:"):
            v = stripped.split(":", 1)[1].strip()
            if "NOT_PUBLISHED" in v or "NOT PUBLISHED" in v:
                verdict = "NOT_PUBLISHED"
            elif "PUBLISHED" in v:
                verdict = "PUBLISHED"
            break

    return LiteratureResult(verdict=verdict, raw=block)
