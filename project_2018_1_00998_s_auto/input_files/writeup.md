# Spatially Resolving CO(2–1) Absorption Toward PKS1740−517: One Absorber or Two?

## Abstract

PKS1740−517 shows CO(2–1) absorption at z = 0.44, but whether this absorption arises from a single foreground screen or from spatially distinct absorbing clouds is unknown. This thesis uses the existing 0.034″-resolution ALMA Band 4 long-baseline data (project 2018.1.00998.S, calibrated measurement set and QA2 products) to test this question directly, without new observations. The continuum (145–149 GHz) will be imaged to determine, as an open empirical outcome, whether the source resolves into one compact core or multiple components (core+lobe / double nucleus). CO(2–1) absorption (159.0–160.9 GHz) will then be extracted against each identified continuum sightline and compared in centroid velocity, depth, and FWHM. Agreement across sightlines supports a single uniform screen; significant offsets or absorption present on only one component support spatially distinct absorbers. If the source is unresolved, the result is reported as a bounded null result at the achieved resolution rather than a failure. The analysis uses only archival pipeline-calibrated products, standard CASA imaging/self-calibration, and `imfit`/Gaussian line fitting — scoped to be completed by one student in one semester.

## Work Plan

**1. Data prep:** Retrieve the calibrated MS and QA2 products (OUS uid://A001/X133d/X18e9) from the archive; verify QA2 pipeline pass. Confirm line IDs via Splatalogue at z = 0.44 (CO(2–1) rest 230.538 GHz → ≈160.10 GHz), noting CN and HC₃N features in 157.0–159.0 GHz. Fixes continuum windows (145.0–149.0 GHz) vs. line windows (157.0–160.9 GHz).

**2. Continuum imaging:** `tclean` on the 145–147 and 147–149 GHz windows near native 0.034″ resolution, Briggs robust = 0.5 (compare 0 / −0.5 if needed), automasking/interactive cleaning to ~thermal noise (0.0119 mJy/bm). Morphology (single core vs. resolved core+lobe/double nucleus) is treated as an open result.

**3. Self-calibration:** Phase-only self-cal (`gaincal`, `calmode='p'`) on the continuum core, starting `solint='inf'` and shortening if stable. Pre-registered per-round acceptance test: keep a round only if dynamic range improves ≥10–20% and per-antenna phase solutions converge at SNR ≥3; run up to 3 rounds, stop at first failure, adopt last passing round. No amplitude self-cal. If phase self-cal fails on round 1, fall back to modest uv-tapering (~2–4× native beam) as a secondary, lower-priority contingency.

**4. Component identification:** Fit the best continuum image with `imfit` (position, flux, size) at ≥5σ. Two-plus components → separate sightlines; unresolved → single-aperture analysis as a valid base case.

**5. Cube imaging & extraction:** `tclean` the 159.0–160.9 GHz window in cube mode at native 1.84 km/s resolution (clean to ~0.44 mJy/bm scaled sensitivity), using the adopted continuum weighting/self-cal. Extract spectra at each component (or single aperture); normalize absorption depth using the 146–149 GHz continuum fit.

**6. Line fitting:** Fit each spectrum with a single Gaussian (minimal multi-component if needed) for centroid velocity, peak depth/optical depth, and FWHM, at native resolution where S/N allows, else binned to 5–10 km/s (documented explicitly).

**7. Comparison:** Compare velocities/depths/FWHM across sightlines qualitatively — consistent values → single foreground screen; significant offsets or one-sided detection → spatially distinct absorbers; single aperture → bounded null result, explicitly noting spatial discrimination was not possible at the achieved resolution.

**Anticipated deliverables/plots:** final continuum image(s) with `imfit` component table; CO(2–1) cube and per-component spectra with Gaussian fit parameters/uncertainties; a summary figure overlaying extracted absorption spectra on the continuum map; a written comparison of centroid velocity, depth, and FWHM across sightlines, framed against the self-cal/tapering decisions and resolution actually achieved.

## Background Reading

- No directly relevant prior citations are available for this dataset. A literature check found no published analysis of this project's long-baseline CO(2–1) data (project 2018.1.00998.S has no linked publications in the ALMA archive); the absorption line's prior detection is referenced only as motivation for the observation, not as a citable dataset publication.
