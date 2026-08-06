# Mapping Interaction-Driven Dense-Gas Chemistry Across the NGC 4567/4568 Tidal Overlap Zone

## Abstract

NGC 4567/4568 (VV_219) is a Virgo-Cluster galaxy pair caught mid-merger, with a tidal "overlap" region where the two disks physically collide, distinct from each galaxy's nuclear and disk gas. This thesis asks whether tidally driven compression/shocks in that overlap zone measurably alter dense-gas chemistry and excitation relative to undisturbed disk gas — a local, low-z analog for dense-gas physics invoked in high-z mergers. Using archival, pipeline-calibrated ALMA Band 3 data (project 2013.1.01332.S, OUS `uid://A001/X144/X81`; ~1.14″/~90 pc resolution), the student builds moment-0 maps of four dense-gas/PDR tracers (HCN, HCO+, HNC J=1–0; CCH N=1–0) and spatially resolved line-ratio maps (HCN/HCO+, HCN/HNC, HCN/CCH) across empirically defined nuclei, bridge, and disk regions. Because this is a 12-m-only observation with no ACA/total-power data, a maximum-recoverable-scale (MRS) check precedes all science analysis to assess whether extended disk emission risks being resolved out relative to compact bridge/nuclear emission — a risk that could manufacture or mask the very contrast being tested. The analysis is scoped entirely to CASA processing of the existing archival products, achievable by one student in a semester-to-year thesis, with no dependence on external multiwavelength datasets.

## Work Plan

**1. Acquisition/inspection:** Download the calibrated measurement set and QA2 image cubes for 2013.1.01332.S (OUS `uid://A001/X144/X81`). Read the QA2 report for beam, sensitivity, and flags; confirm the four target lines (HCN, HCO+, HNC J=1–0, CCH N=1–0) against Splatalogue at z≈0.0075, noting the 99–102 GHz windows are continuum-dominated.

**2. MRS/missing-flux check:** In CASA, extract the uv-distance distribution (`plotms`), find the shortest baseline, and compute MRS ≈ 0.6λ/b_min. Compare to the angular scale of nuclei/bridge/disk apertures. Report explicitly as a standalone result and carry forward as a named caveat regardless of outcome.

**3. Imaging:** Use `tclean` (Briggs robust ~0.5, ~1.14″ common restoring beam) to image all four lines, starting from QA2 cubes and re-imaging only where artifacts require it. Image continuum separately from line-free channels; continuum-subtract each line cube (`uvcontsub`/`imcontsub`).

**4. Moment maps:** Generate moment-0 maps per tracer with `immoments`, masking at a fixed 3–5σ per-channel threshold, in consistent Jy/beam km/s units. *Key deliverable: four calibrated moment-0 maps.*

**5. Region definition:** Using continuum + HCN moment-0 maps, define nuclei (peak thresholds), bridge (fixed HCN contour), and disk (remaining extended emission) with documented, reproducible criteria.

**6. SNR triage:** Measure per-beam SNR of each moment-0 map per region; apply a pre-registered ≥5σ threshold. If CCH/HNC fail in the bridge, fall back to a coarser two-region scheme (nuclei+disk vs. bridge).

**7. Line-ratio maps:** Divide co-registered, matched-resolution moment-0 maps pixel-by-pixel (HCN/HCO+, HCN/HNC, HCN/CCH), propagating errors and masking sub-threshold pixels. Tabulate median and IQR per region. *Key deliverable: three spatially resolved ratio maps plus a summary table of regional medians/IQRs — the thesis's primary result.*

**8. Statistical comparison:** Sample one value per independent beam area per region; apply Mann-Whitney U/KS tests between regions (e.g., bridge vs. disk). Treat this as a supplementary, low-power confirmatory check, not the primary evidence — interpretive weight rests on the maps and descriptive effect sizes.

**9. Interpretation:** Interpret ratio variation across regions as evidence for/against tidally driven chemistry/excitation changes, qualified by three caveats: (a) single-transition ratios can't isolate excitation/optical-depth/abundance effects; (b) beam-sampling reduces but doesn't eliminate spatial autocorrelation; (c) the Step 2 MRS/missing-flux result must be weighed before attributing any contrast to chemistry rather than differential flux recovery, especially for CCH. All CASA scripts, thresholds, and region definitions are retained for full reproducibility.

## Background Reading

- No directly relevant prior publications were identified for this dataset: an archive and literature search found no peer-reviewed paper analyzing ALMA project 2013.1.01332.S (VV_219/NGC 4567/4568 dense-gas tracers), and no self-citation is recorded in the ALMA archive for this project.
