"""Stage 13 runner: real ALMA data -> full analysis -> AASTeX PDF paper.

Unlike every earlier stage (which only ever produced markdown planning
documents from an LLM), this is the first entrypoint in this repo that
actually downloads real ALMA science-data FITS products, runs real analysis
code against them (analysis.py -- moment maps, beam-scaled aperture
photometry, an HCN luminosity/dense-gas-mass conversion, a central-
depression metric), and compiles a real AASTeX-formatted PDF whose Results
section is grounded in those real measurements, not a placeholder.

Assumes `data_description.md` already exists for this project (per Stage 4's
convention -- manually sourced, not automated); if `idea.md`/`methods.md`/
`literature.md` don't exist yet, this runs Stage 5/6/7 to produce them first,
identically to run_pipeline.py.

Usage:
    python run_full_paper.py <project_dir> <project_code> <pi> <target> [n_iterations]

Makes real, cost-incurring `claude` CLI calls and a real network download --
run deliberately.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import warnings

warnings.filterwarnings("ignore")

from astropy.io import fits

from alma_download import fetch_science_products
from analysis import run_analysis
from idea_loop import run_idea_loop, score_tractability
from latex_paper import build_aastex_document, compile_pdf
from literature import check_published
from methods import generate_methods
from paper import assemble_paper_with_results
from state import (
    DESCRIPTION_FILE,
    IDEA_FILE,
    LITERATURE_FILE,
    METHODS_FILE,
    figures_dir,
    raw_data_dir,
    read_state_file,
    write_state_file,
)

# Adopted for NGC 4429 specifically -- see analysis.py's module docstring on
# why these are passed in explicitly rather than hardcoded as module
# constants. Distance: Virgo Cluster mean, NGVS SBF catalog (Cantiello et al.
# 2018, ApJ 856, 126). Systemic velocity: heliocentric, from NED.
NGC4429_DISTANCE_MPC = 16.5
NGC4429_SYSTEMIC_VEL_KMS = 1104.0

EXTRA_CITATIONS = [
    "Gao, Y. & Solomon, P. M. 2004, ApJS, 152, 63 (dense-gas mass conversion factor, alpha_HCN)",
    "Cantiello, M. et al. 2018, ApJ, 856, 126 (NGVS Virgo Cluster surface-brightness-"
    "fluctuation distance catalog; adopted distance)",
]

SOFTWARE_NOTE = (
    "This paper's Abstract, Introduction, Methods, Results, and Conclusions text was drafted "
    "by an LLM-based automated pipeline (this repository's Stage 5/7/13), conditioned strictly "
    "on real measurements from the analysis code described in Methods -- no simulated or "
    "placeholder numbers appear in the Results section. The underlying analysis used "
    "astropy, spectral-cube, radio-beam, and photutils (Python). This is a pilot/demonstration "
    "output and has not been independently peer reviewed; a domain expert should verify every "
    "quantitative claim before any further use."
)


def _ensure_idea_methods_literature(project_dir: str, project_code: str, pi: str, target: str, n_iterations: int):
    data_description = read_state_file(project_dir, DESCRIPTION_FILE)

    lit_path = Path(project_dir) / "input_files" / LITERATURE_FILE
    if not lit_path.exists():
        print("Running literature/published check...")
        result = check_published(project_code, pi, target, data_description)
        write_state_file(project_dir, LITERATURE_FILE, result.raw + "\n")
        if result.verdict == "PUBLISHED":
            raise SystemExit(
                "This project's data appears to already be PUBLISHED -- this script is for "
                "producing a new pilot paper from an unpublished dataset. See literature.md."
            )

    idea_path = Path(project_dir) / "input_files" / IDEA_FILE
    methods_path = Path(project_dir) / "input_files" / METHODS_FILE
    if not idea_path.exists() or not methods_path.exists():
        print(f"Running idea loop ({n_iterations} iterations) + methods generation...")
        idea_result = run_idea_loop(data_description, n_iterations=n_iterations)
        score = score_tractability(data_description, idea_result.final_idea)
        print(score)
        write_state_file(project_dir, IDEA_FILE, idea_result.final_idea + "\n")
        methods_text = generate_methods(data_description, idea_result.final_idea)
        write_state_file(project_dir, METHODS_FILE, methods_text + "\n")

    return (
        read_state_file(project_dir, IDEA_FILE),
        read_state_file(project_dir, METHODS_FILE),
        read_state_file(project_dir, LITERATURE_FILE),
    )


def main() -> int:
    if len(sys.argv) < 5:
        print("Usage: python run_full_paper.py <project_dir> <project_code> <pi> <target> [n_iterations]")
        return 1

    project_dir, project_code, pi, target = sys.argv[1:5]
    n_iterations = int(sys.argv[5]) if len(sys.argv) > 5 else 4

    idea, methods, literature = _ensure_idea_methods_literature(project_dir, project_code, pi, target, n_iterations)

    print(f"\nDownloading real ALMA science products for {project_code} / {target}...")
    fetched = fetch_science_products(project_code, target, raw_data_dir(project_dir))
    print(f"  member OUS: {fetched.member_ous_uid}")
    print(f"  continuum: {fetched.continuum_fits}")
    print(f"  cube: {fetched.cube_fits}")
    if not fetched.continuum_fits or not fetched.cube_fits:
        raise SystemExit("Need both a continuum image and a line cube for this analysis; aborting.")

    with fits.open(fetched.continuum_fits) as hdul:
        header = hdul[0].header
        ra_deg, dec_deg = header["CRVAL1"], header["CRVAL2"]

    print("\nRunning real analysis (moment maps, aperture photometry, luminosity/mass conversion)...")
    results = run_analysis(
        project_dir, fetched.continuum_fits, fetched.cube_fits, ra_deg, dec_deg, target,
        distance_mpc=NGC4429_DISTANCE_MPC, systemic_velocity_kms=NGC4429_SYSTEMIC_VEL_KMS,
    )
    print(f"  continuum RMS: {results['continuum']['rms_mjy_beam']:.4f} mJy/beam")
    print(f"  HCN central-depression interpretation: {results['hcn']['central_depression_interpretation']}")

    print("\nWriting real-results paper sections (Claude calls)...")
    sections = assemble_paper_with_results(idea, methods, literature, results)
    print(f"  title: {sections['title']}")

    print("\nAssembling AASTeX document and compiling PDF...")
    figs_dir = figures_dir(project_dir)
    figures = [
        {"path": str(figs_dir / "continuum.png"), "label": "fig:continuum",
         "caption": "ALMA Band 3 continuum image of the NGC 4429 nucleus, with the three "
                    "beam-scaled photometry apertures (1, 2, 3 beam radii) overlaid."},
        {"path": str(figs_dir / "hcn_moments.png"), "label": "fig:moments",
         "caption": "HCN(1-0) moment 0 (integrated intensity), moment 1 (velocity), and "
                    "moment 2 (velocity dispersion) maps, masked at the 3-sigma per-channel level."},
        {"path": str(figs_dir / "hcn_pv_diagram.png"), "label": "fig:pv",
         "caption": "Position-velocity cut through the nucleus along the image R.A. axis "
                    "(no disk position angle was available from the archive metadata)."},
    ]

    tex = build_aastex_document(
        title=sections["title"],
        abstract=sections["abstract"],
        introduction=sections["introduction"],
        methods=sections["methods"],
        results=sections["results"],
        conclusions=sections["conclusions"],
        references_text=sections["references"],
        figures=figures,
        extra_citations=EXTRA_CITATIONS,
        software_note=SOFTWARE_NOTE,
    )

    pdf_build_dir = Path(project_dir) / "pdf_build"
    pdf_build_dir.mkdir(parents=True, exist_ok=True)
    for fig in figures:
        shutil.copy(fig["path"], pdf_build_dir / Path(fig["path"]).name)

    pdf_path = compile_pdf(tex, pdf_build_dir, basename="paper")
    final_pdf = Path(project_dir) / "paper.pdf"
    shutil.copy(pdf_path, final_pdf)

    print(f"\n[DONE] Paper PDF written to {final_pdf}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
