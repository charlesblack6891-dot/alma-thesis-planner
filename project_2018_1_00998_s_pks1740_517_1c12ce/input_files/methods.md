**1. Data retrieval and inventory**

Have the student log into the ALMA Science Archive and pull down the full data package for member OUS `uid://A001/X133d/X18e9` (project 2018.1.00998.S, target PKS1740-517). This includes the pipeline-calibrated measurement set, the QA2 weblog, and the delivered QA2 image/cube products. Have them read the QA2 weblog first — it records the exact pipeline/CASA version used for calibration, the final flagging summary, and the achieved sensitivities, which the student will need later to sanity-check their own re-imaging. Since long-baseline Band 4 data are involved, have the student confirm from the weblog whether any self-calibration or phase referencing issues were flagged, since these affect how aggressively they can re-image at full resolution.

**2. Software environment**

Install the CASA version matching (or the closest supported version to) the one recorded in the QA2 weblog, so that pipeline calibration tables and MS structure remain compatible with re-imaging commands (`tclean`, `imfit`, `uvmodelfit`, `specfit`, `exportfits`, etc.). Keep a lab notebook of every CASA task and parameter set used, since imaging at 0.034″ resolution is sensitive to weighting choices and small parameter changes can shift apparent source structure.

**3. Continuum imaging of the line-free windows**

Use only the two spectral windows identified as continuum-only at this redshift (observed 145.0–147.0 GHz and 147.0–149.0 GHz; note these correspond to rest-frame ≈208.8–214.6 GHz under the assumed z = 0.44, and this line-free identification should also be spot-checked against Splatalogue before being treated as final). Flag any residual line contamination if found. Run `tclean` in `specmode='mfs'` on the combined line-free channels to produce the deepest possible continuum map at native long-baseline resolution, targeting the archive-quoted continuum sensitivity of 0.0119 mJy/bm as a benchmark for the student's own image RMS. Experiment with Briggs weighting (a robust parameter scan, e.g., robust = 0, 0.5, 1) to balance resolution against sidelobe/noise behavior at this extreme baseline length, and document how the apparent source morphology changes across the scan.

**4. Continuum source characterization**

On the best continuum image, have the student search for compact structure at the phase center and identify all significant peaks above, e.g., 5–7σ. For each candidate component, fit a point-source or Gaussian model directly in the image plane with `imfit`, and cross-check with a uv-plane fit (`uvmodelfit`) using one- and two-component point-source models, comparing fit residuals and reduced chi-squared to determine whether a single-component or double-component model is statistically preferred. Record best-fit positions (RA/Dec), peak flux densities, and formal position uncertainties (beam-size/SNR-scaled) for each component — these positions are the sightlines used in the next step. This directly tests the "double radio core" scenario motivating the project.

**5. Verification of the CO(2–1) line identification**

Before touching the line-bearing window, have the student independently verify the line identification in Splatalogue: look up CO(2–1) rest frequency (230.538 GHz) and confirm that, under the quoted host redshift z = 0.44 (observed = rest/1.44), the expected observed frequency (≈160.10 GHz, provisional) falls inside the delivered 159.0–160.9 GHz spectral window. Have the student note explicitly in their methods write-up that this identification and frequency are provisional/assumed pending this check, and flag (but do not attempt to observationally resolve) the CN and HC₃N lines noted as plausible serendipitous contaminants in the neighboring 157.0–159.0 GHz window, so that any spectral features near the CO(2–1) window are correctly attributed.

**6. Spectral cube imaging**

Image the 159.0–160.9 GHz spectral window as a full cube with `tclean` in `specmode='cube'`, using the native/delivered velocity resolution (≈1.84 km/s channels) or a modest binning if SNR requires it, and using the same weighting scheme validated in step 3 for consistency with the continuum astrometry. Continuum-subtract the cube (`uvcontsub` or image-plane subtraction using nearby line-free channels within the same window, if any) so that absorption is measured relative to the correct local continuum level rather than the broadband continuum from step 3.

**7. Absorption spectrum extraction at each continuum peak**

At the position of each continuum component identified in step 4, extract a spectrum from the continuum-subtracted cube (single-pixel or small-aperture extraction matched to the synthesized beam) using CASA's `imval`/`specflux`-type tools or a Python/`spectral-cube` post-processing script. Normalize each extracted spectrum by the local continuum flux density at that position (from the step-3/step-4 continuum fit) to produce an optical-depth-like absorption profile (line depth relative to continuum) for each sightline.

**8. Line profile fitting and comparison**

Fit each extracted absorption profile with a Gaussian (or multi-Gaussian, if profiles are clearly multi-component) using `specfit` or a Python least-squares routine, deriving for each sightline: peak absorption depth (or apparent optical depth), centroid velocity (relative to the assumed systemic redshift z = 0.44), and FWHM line width, each with formal fit uncertainties propagated from the cube RMS. Tabulate these parameters side by side for each continuum component.

**9. Geometric interpretation**

Compare the fitted parameters across sightlines using their formal uncertainties: if centroid velocities, widths, and depths agree within errors between components, treat this as evidence for a single, spatially uniform absorbing screen (consistent with a compact circumnuclear disk/torus); if they differ significantly, treat this as evidence that the absorption differs between components (consistent with extended, merger-disturbed gas straddling a double core). Where only one continuum component is robustly detected, adjust the analysis to report a single-sightline absorption profile and state that the two-component test could not be performed. Present the final continuum map, the extracted/fitted absorption spectra per sightline, and the tabulated comparison of centroid velocity, depth, and width as the core results answering the one-screen-versus-two-screen question.
