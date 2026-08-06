# Spatio-Chemical Differentiation in the HH 212 Outflow at ACA Resolution: A Coarse Lobe-Scale Line-Ratio and Velocity-Structure Comparison

## Abstract

Molecular outflows from young protostars are thought to comprise a fast, collimated jet and a slower, shocked cavity wall, each traced by distinct chemistry and kinematics — but whether this differentiation survives at the coarse resolution of compact-array data is untested. This thesis uses the six ACA member OUS tunings covering HH 212 (`Xf93`, `Xfa6`, `Xfb9`, `Xfcc`, `Xfdf`, `Xff2`; ~292–361 GHz, Band 7, pipeline-calibrated QA2 cubes) to test jet-vs-wall spatio-chemical differentiation in a single well-studied outflow, deliberately narrowing a broader multi-source survey concept to one source for tractability. As a go/no-go step, the student first checks HH 212's bipolar lobe extent against the ACA's ~30″ single-pointing primary beam; if one lobe falls outside the beam, analysis is restricted to the covered lobe and reported as a limitation. Four candidate tracers — SiO 8–7, ¹²CO 3–2, SO 8₈–7₇, and CH₃OH 7₀–6₀ A⁺ — are verified against the full Splatalogue line list (not assumed from the archive's own "generated from general knowledge" annotation) before being finalized. Using these confirmed lines, the student compares line ratios (SiO/CH₃OH, CO/SO) and velocity structure across a handful of beam-sized apertures stepped along the jet axis, testing whether jet tracers stay centrally peaked and kinematically broad while wall tracers appear flatter/offset and narrower. Given the ~3.2–4″ beam and ~30″ field, this yields only ~3–4 independent apertures per lobe; the result is explicitly framed as a coarse gradient check, not a resolved spatial profile. The analysis uses only standard CASA workflows on one already-calibrated archival dataset, with no new observations.

## Work Plan

**Data assembly:** Retrieve calibrated MSs and QA2 cubes for all six member OUS; build a lookup table of frequency windows, beam size, and channel width per tuning; maintain a CASA logbook throughout.

**Step 1 — FOV go/no-go:** Compare HH 212's known NE–SW lobe extent (source at RA/Dec ≈ 85.964, −1.048) against a Gaussian primary-beam model (~30″ FWHM, single pointing). Both lobes covered → two-sided analysis; one lobe outside half-power point → restrict to the covered lobe and report as a scope constraint.

**Step 2 — Splatalogue verification:** Query Splatalogue/`slsearch` around each of the four rest frequencies (SiO 347.331 GHz, ¹²CO 345.796 GHz, SO 344.311 GHz, CH₃OH 338.409 GHz) within a window of a few channel widths (~0.94–1.1 km/s), cross-checked against HH 212's systemic velocity and outflow velocity range (up to ~100 km/s wings). Severe unresolvable blends are dropped; flagged lines proceed with a moment-map sanity check. Finalize the tracer set only after this pass.

**Step 3 — Imaging and moment maps:** For each confirmed line, extract the relevant spw and, where QA2 cubes are inadequate, re-image with `tclean` (Briggs robust ~0.5). Continuum-subtract with `uvcontsub`/`imcontsub`, then produce moment 0/1/2 maps via `immoments` (3–5σ masking). Visually confirm morphology against the known jet/lobe geometry.

**Step 4 — Aperture grid:** Using the strongest tracer's moment 0 map, lay ~3–4 non-overlapping circular apertures per lobe (diameter matched to the largest synthesized beam, ~3.2–4″) outward from the driving source to the lobe edge (per Step 1 outcome). Record positions in arcsec and physical units.

**Step 5 — Spectral extraction:** Extract integrated spectra per aperture/line (`specflux`/`imstat`), drop non-detections rather than substituting tracers, and fit line profiles (`specfit` or Gaussian fitting) for peak velocity, FWHM, and integrated intensity; separately quantify high-velocity wing strength (e.g., flux beyond ~10 km/s of line center).

**Step 6 — Ratio and kinematic comparison:** Compute SiO/CH₃OH and CO/SO ratios with propagated uncertainties per aperture; plot ratio vs. distance from source to test jet-centrally-peaked vs. wall-flatter/offset behavior. Compare peak velocity, line width, and wing fraction between jet and wall tracers at matched positions.

**Step 7 — Synthesis:** Report the aperture table, moment maps, spectra, and ratio/kinematic trends as a lobe-averaged, coarse-sampled result. State explicitly what spatial scale of differentiation the ACA beam can and cannot resolve, include the Step 1 and Step 2 outcomes as part of the methodological record, and limit any comparison to higher-resolution literature to one or two qualitative sentences (not a quantitative input).

**Key anticipated products:** primary-beam/lobe-coverage overlay figure; Splatalogue verification table; continuum-subtracted moment 0/1/2 maps for each confirmed line; aperture-position table; line-ratio-vs-position and line-width/peak-velocity-vs-position plots for both lobes; summary table of per-aperture measurements and dropped apertures.

## Background Reading

- (No archive-linked publications recorded for this dataset; no directly relevant peer-reviewed citations identified.)
