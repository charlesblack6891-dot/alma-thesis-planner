**1. Data retrieval and preparation**

Download the pipeline-calibrated measurement set(s) and QA2 image products for project 2018.1.00998.S, member OUS `uid://A001/X133d/X18e9`, from the ALMA Science Archive. Confirm the calibration pipeline version and weblog pass basic QA2 checks (no flagged antennas dominating the array, reasonable bandpass/phase solutions) before proceeding — this is a sanity check on delivered data, not a re-derivation of calibration. Load the measurement set into a working CASA environment (matching the pipeline version recommended in the weblog) and inspect the QA2 continuum and cube images to get a first look at source structure, noise levels, and the location of the CO(2–1) absorption relative to the QA2 report.

Confirm line identifications against Splatalogue using the quoted host redshift z = 0.44: check that CO(2–1) rest 230.538 GHz falls at ≈160.10 GHz within the 159.0–160.9 GHz window, and note the CN N=2–1 and HC₃N J=25–24 features that may fall in the 157.0–159.0 GHz window. This fixes which spectral windows are treated as continuum-only (145.0–149.0 GHz) versus line windows (157.0–160.9 GHz) for the rest of the analysis.

**2. Continuum imaging (145–149 GHz windows)**

Using `tclean` in CASA, image the two continuum spectral windows (145.0–147.0 and 147.0–149.0 GHz), starting from the QA2 continuum image as a reference for expected flux and structure. Use a robust weighting (start with Briggs robust = 0.5 as a compromise between resolution and sensitivity, and compare against robust = 0 or −0.5 if the beam sidelobes or sensitivity require it) to image at or near the native 0.034″ resolution. Clean interactively or with an automasking threshold (e.g., `auto-multithresh`) down to a few times the expected thermal noise (0.0119 mJy/bm), inspecting residuals at each major cycle.

Treat the resulting continuum morphology — single compact core, resolved core+lobe, or double nucleus — as an open empirical result. Do not assume a particular morphology going in.

**3. Self-calibration**

Because 0.034″ corresponds to baselines long enough that phase decorrelation is the expected limiting factor, apply phase-only self-calibration on the continuum core as the default correction strategy:

- Construct an initial clean-component model of the continuum from step 2.
- Solve for phase-only gain corrections (`gaincal`, `calmode='p'`) on a solution interval chosen to balance SNR per solution against decorrelation timescale (start with `solint='inf'` per scan, then shorten if solutions remain stable).
- Apply the solution, re-image, and evaluate.

Before running self-cal, fix the acceptance criterion for each round: a round is kept only if it improves image dynamic range (peak/rms) by a pre-specified margin (e.g., ≥10–20%) *and* the derived per-antenna phase solutions converge with SNR ≥ 3 over the chosen solution interval. Run up to three rounds of phase self-cal, shortening the solution interval each round if the previous round passed. Stop as soon as a round fails the test, and adopt the last passing round's image as the working continuum map. Do not attempt amplitude self-calibration — the continuum is not bright enough on these baselines to support it reliably within a single thesis project.

If phase self-cal does not pass the acceptance test on the first round, apply a modest uv-taper (e.g., targeting ~2–4× the native beam) as a secondary, lower-priority fallback to recover a usable, if lower-resolution, continuum detection, and proceed with the analysis at that resolution instead.

**4. Continuum component identification**

Fit the best-achievable continuum image with `imfit` to identify discrete source components (position, integrated flux, deconvolved size) above a chosen significance threshold (e.g., 5σ). Record however many components are found:

- If the map resolves into two or more distinct components, treat each as a separate sightline for the absorption analysis in step 5.
- If the map does not resolve into distinct components (a single unresolved or marginally resolved core), proceed with a single-aperture analysis using the full continuum region as one sightline. This is a valid base-case outcome, not a failure of the method.

**5. CO(2–1) cube imaging and spectral extraction**

Image the 159.0–160.9 GHz spectral window with `tclean` in cube mode at native spectral resolution (1.84 km/s channels), using the same weighting/self-cal solutions established for the continuum. Clean to a noise level consistent with the quoted line sensitivity (0.44 mJy/bm at 10 km/s, scaled appropriately for the native channel width).

At each continuum component position identified in step 4 (or the single aperture if unresolved), extract a spectrum from the CO(2–1) cube using an aperture matched to the (restored) beam or to the fitted component size. Normalize the absorption depth in each spectrum using the corresponding continuum flux from the 146–149 GHz fit at that same position, converting to optical depth or fractional absorption depth as appropriate.

**6. Line profile fitting**

Fit each extracted absorption spectrum with a single Gaussian (or, if the profile is clearly non-Gaussian, a minimal number of Gaussian components sufficient to describe the visible structure) to measure:

- centroid velocity (relative to the systemic redshift z = 0.44),
- peak absorption depth / optical depth,
- FWHM.

Perform fits at native 1.84 km/s resolution where per-channel S/N supports it; where S/N is too low, spectrally bin to a coarser resolution (e.g., 5–10 km/s) as a documented, explicit fallback, and note which components required binning.

**7. Comparative analysis**

Compare the fitted centroid velocities, depths, and FWHM across all identified sightlines (continuum components or single aperture):

- If velocities and depths agree within their fitted uncertainties across all components, report this as consistent with a single foreground absorbing screen covering the source uniformly.
- If centroid velocities differ significantly between components, or absorption is detected against only one component but not another, report this as evidence for spatially distinct absorbers rather than a single uniform screen.
- If only one component is identified (unresolved case from step 4), report the single-aperture absorption profile and its kinematics as a bounded result at the achieved angular resolution, explicitly stating that spatial discrimination between one and two absorbers was not possible at this resolution.

Present this comparison qualitatively (e.g., stating measured velocity/depth offsets and their significance) rather than through formal kinematic model-fitting, since the number of resolvable spatial components is too small to support statistical model discrimination.

**8. Deliverables**

Produce, for the thesis: (a) the final continuum image(s) with `imfit` component table; (b) the CO(2–1) cube and per-component extracted spectra with Gaussian fit parameters and uncertainties; (c) a summary figure overlaying absorption spectra from each identified sightline against the continuum map; (d) a written comparison of centroid velocity, depth, and FWHM across sightlines addressing whether the data are consistent with one or two spatially distinct molecular absorbers toward PKS1740−517, framed relative to the self-cal/tapering decisions and resolution actually achieved.
