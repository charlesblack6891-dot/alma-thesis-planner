"""Real ALMA science-data download (Stage 13 support).

Everything upstream of this module (Stages 1-11) works from metadata and
LLM-written text only -- nothing in this repo has ever downloaded or looked
at actual ALMA visibility/image data before. This module queries the public
ALMA Science Archive TAP service for a given proposal, finds the pipeline's
own already-imaged, science-ready FITS products (continuum image + one
spectral-line cube) for a public (non-proprietary) project, and downloads
them -- no CASA calibration or imaging is performed here or anywhere in this
repo; we only fetch products the ALMA pipeline already produced and released.

Requires the `netfix` SSL workaround for this development machine's AVG
Antivirus TLS interception (see netfix.py's docstring).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import requests
from astroquery.alma import Alma

import netfix

_PATCHED = False


class LegacyDeliveryError(RuntimeError):
    """Raised when a member OUS has no per-product pipeline-imaging datalink
    service at all -- only bundled '#package' delivery tarballs and/or raw
    '#progenitor' ASDM data are exposed, not individually addressable,
    already-imaged FITS products. This is ALMA's pre-pipeline delivery
    format (roughly Cycle 0/1, ~2011-2013, before the per-product datalink
    convention this module relies on existed); confirmed live against
    2011.0.00754.S (Sombrero), whose delivery is exactly this shape."""


def _ensure_patched() -> None:
    global _PATCHED
    if not _PATCHED:
        netfix.patch_alma(Alma)
        _PATCHED = True


@dataclass
class AlmaProduct:
    filename: str
    url: str
    content_length: int | None
    semantics: str


def find_member_ous_uids(proposal_id: str, target_name: str | None = None) -> list[str]:
    """Look up the member_ous_uid(s) for a public ALMA proposal, optionally
    filtered to one target (a proposal can cover several targets/pointings).
    """
    _ensure_patched()
    where = f"proposal_id = '{proposal_id}' AND data_rights = 'Public' AND science_observation = 'T'"
    if target_name:
        where += f" AND target_name = '{target_name}'"
    q = f"SELECT DISTINCT member_ous_uid FROM ivoa.obscore WHERE {where}"
    t = Alma.query_tap(q).to_table()
    return [str(row["member_ous_uid"]) for row in t]


def list_science_files(member_ous_uid: str) -> list[AlmaProduct]:
    """List every individual file inside a member OUS's downloadable
    packages (expanding the '#this' and '#auxiliary' tarballs via the
    datalink service) without downloading anything. Raw/progenitor ASDM data
    and #cutout placeholder rows are excluded -- we only want already-imaged
    FITS products.
    """
    _ensure_patched()
    res = Alma.datalink.run_sync(member_ous_uid)
    top = res.to_table()

    service_defs = {
        adhoc.ID: adhoc
        for adhoc in res.iter_adhocservices()
        if Alma.is_datalink_adhoc_service(adhoc)
    }
    if not service_defs:
        semantics_found = sorted(set(str(s) for s in top["semantics"])) if len(top) else []
        raise LegacyDeliveryError(
            f"{member_ous_uid} exposes no per-product pipeline-imaging datalink service -- only "
            f"{semantics_found or '(nothing)'} is available (generic bundled delivery tarballs "
            "and/or raw ASDM data, not individually addressable science-ready FITS images). This "
            "is ALMA's pre-pipeline delivery format, typical of Cycle 0/1 projects (~2011-2013); "
            "this module can only fetch the modern, per-product pipeline-imaging delivery "
            "convention used from roughly Cycle 2 onward."
        )

    products: list[AlmaProduct] = []
    for row in top:
        sem = str(row["semantics"])
        sd = row["service_def"]
        if sd and sd in service_defs:
            if sem == "#auxiliary":
                continue  # calibration tables/weblogs/QA reports, not science FITS
            url = Alma.get_adhoc_service_access_url(service_defs[sd])
            file_id = url.split("ID=")[1]
            sub = Alma.datalink.run_sync(file_id).to_table()
            for r2 in sub:
                sem2 = str(r2["semantics"])
                if sem2 in ("#cutout",) or not r2["access_url"]:
                    continue
                url2 = str(r2["access_url"])
                products.append(
                    AlmaProduct(
                        filename=url2.rsplit("/", 1)[-1],
                        url=url2,
                        content_length=int(r2["content_length"]) if r2["content_length"] else None,
                        semantics=sem2,
                    )
                )
        elif sem == "#progenitor":
            continue  # raw ASDM data -- never needed, we only use pipeline image products
        elif sem == "#auxiliary":
            continue

    return products


def pick_continuum_and_cube(products: list[AlmaProduct]) -> tuple[AlmaProduct | None, AlmaProduct | None]:
    """From a member OUS's file list, pick one wideband continuum image and
    one spectral-line cube -- both primary-beam-corrected, preferring the
    self-calibrated version, and preferring the smallest matching file (a
    narrower "representative bandwidth" cube over the full-bandwidth one)
    to keep downloads light.
    """
    cont_re = re.compile(r"\.cont\.I\.(selfcal\.)?tt0\.pbcor\.fits$")
    cube_re = re.compile(r"\.(repBW\.)?I\.(selfcal\.)?pbcor\.fits$")

    def is_cube_name(name: str) -> bool:
        return ".cube." in name or ".repBW." in name

    continuum_candidates = [p for p in products if cont_re.search(p.filename)]
    cube_candidates = [p for p in products if is_cube_name(p.filename) and cube_re.search(p.filename)]

    def best(cands: list[AlmaProduct]) -> AlmaProduct | None:
        if not cands:
            return None
        selfcal = [p for p in cands if "selfcal" in p.filename]
        pool = selfcal or cands
        return min(pool, key=lambda p: p.content_length or float("inf"))

    return best(continuum_candidates), best(cube_candidates)


def download(product: AlmaProduct, dest_dir: str | Path) -> Path:
    """Download one product with the AVG-SSL-intercept workaround, streaming
    to disk. Skips re-downloading if a file of the expected size already
    exists at the destination."""
    _ensure_patched()
    dest = Path(dest_dir) / product.filename
    if dest.exists() and product.content_length and dest.stat().st_size == product.content_length:
        return dest

    session = requests.Session()
    netfix.patch_session(session)
    with session.get(product.url, stream=True, timeout=120) as r:
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    return dest


@dataclass
class FetchedData:
    member_ous_uid: str
    continuum_fits: Path | None
    cube_fits: Path | None


def fetch_science_products(proposal_id: str, target_name: str, dest_dir: str | Path) -> FetchedData:
    """End-to-end: find the member OUS for this proposal/target, pick a
    continuum image and a line cube from its public pipeline products, and
    download both. Raises if no member OUS or no continuum+cube pair is
    found -- callers should treat that as "no usable image products for
    this project," not silently proceed."""
    uids = find_member_ous_uids(proposal_id, target_name)
    if not uids:
        raise ValueError(f"No public member OUS found for {proposal_id} / {target_name}")

    # A proposal can split one target across several member OUS (e.g. one
    # per band/line setup); prefer whichever single member OUS offers BOTH
    # a continuum image and a line cube over one offering only one of them.
    best: tuple[str, AlmaProduct | None, AlmaProduct | None] | None = None
    best_score = -1
    legacy_uids: list[str] = []
    modern_no_match_uids: list[str] = []
    for uid in uids:
        try:
            products = list_science_files(uid)
        except LegacyDeliveryError:
            legacy_uids.append(uid)
            continue
        cont, cube = pick_continuum_and_cube(products)
        score = (1 if cont else 0) + (1 if cube else 0)
        if score > best_score:
            best, best_score = (uid, cont, cube), score
        if score == 2:
            break
        modern_no_match_uids.append(uid)

    if best is None or best_score == 0:
        if legacy_uids and not modern_no_match_uids:
            raise LegacyDeliveryError(
                f"{proposal_id} / {target_name}: all {len(legacy_uids)} public member OUS use "
                "ALMA's pre-pipeline bundled delivery format (generic package tarballs / raw ASDM "
                "data only, no individually downloadable science-ready FITS images) -- typically a "
                "Cycle 0/1 project (~2011-2013). This pipeline only supports the modern, "
                "per-product pipeline-imaging delivery convention (roughly Cycle 2 onward); it "
                "can't fetch usable images for this project regardless of target-name spelling."
            )
        elif legacy_uids and modern_no_match_uids:
            raise ValueError(
                f"{proposal_id} / {target_name}: {len(legacy_uids)} of {len(uids)} public member "
                "OUS use ALMA's unsupported pre-pipeline bundled delivery format, and the "
                f"remaining {len(modern_no_match_uids)} had modern pipeline-imaged products but "
                "none included both a continuum image and a spectral-line cube."
            )
        else:
            raise ValueError(f"No continuum/cube FITS products found for {proposal_id} / {target_name}")

    uid, cont, cube = best
    cont_path = download(cont, dest_dir) if cont else None
    cube_path = download(cube, dest_dir) if cube else None
    return FetchedData(member_ous_uid=uid, continuum_fits=cont_path, cube_fits=cube_path)
