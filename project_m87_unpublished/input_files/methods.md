**1. Data compilation from the literature**

Begin by building a single, well-documented spreadsheet (CSV/Google Sheet, versioned in the thesis Git repository) of every polarization-relevant measurement reported in Aviles Contreras et al., A&A 699, A265 (2025) — the Band 7 (345 GHz) M87 jet polarization paper is the "data" for this project, so treat its extraction with the same care as a raw observation:

- From the paper's tables, transcribe directly any numerically reported values: fractional linear polarization *m*, EVPA (χ), Stokes I/Q/U where given, RM values, and their stated uncertainties, along with the position along the jet (deprojected distance from the core, typically in mas or pc) and/or position angle at which each was measured.
- For quantities given only graphically (e.g., an RM-vs-distance or EVPA-vs-distance plot, or a polarization map), use WebPlotDigitizer (or an equivalent open-source plot digitizer) to extract (x, y) pairs. Calibrate each digitization against the plot's axis tick marks before extracting points, and digitize each panel twice, independently, on different days, to get a digitization-precision estimate; adopt the larger of (digitization scatter, any error bar visible in the plot) as the point's uncertainty.
- Record, for every entry, the source figure/table number and page, so the spreadsheet is auditable against the PDF.
- Tag each measurement with its physical location: core, jet base (sub-kpc), or extended jet (out to the ~kpc scales the paper covers), since the model comparison is a function of position along the jet.

This compiled table (likely 15–40 usable position/RM/EVPA points, consistent with the paper's stated spatial resolution and S/N cuts) is the entire empirical input to the thesis; no ALMA archive access, calibration, or imaging is performed.

**2. Formulating the candidate magnetic-field models**

Implement, in Python, closed-form predictions for EVPA(s) and RM(s) as a function of deprojected distance *s* (and, where the paper resolves transverse structure, transverse offset across the jet width) for four field geometries, using standard synchrotron-polarization and Faraday-screen formulas from the relativistic-jet literature (e.g., Blandford & Königl 1979 for jet field scaling; Blandford 1993 and Lyutikov, Pariev & Gabuzda 2005 for RM signatures of helical/toroidal fields threading a jet; Pushkarev et al. and Gabuzda et al. for the standard "RM sign-reversal across the jet" helical-field test):

- *Helical field*: toroidal component scaling as B_φ ∝ 1/r and poloidal component as B_z ∝ 1/r², combined with a pitch angle parameter; predicts a monotonic RM gradient transverse to (or along) the jet and an EVPA that rotates smoothly with position, with a specific sign tied to the helicity handedness.
- *Purely toroidal field*: EVPA locked parallel/perpendicular to the local jet axis (no systematic rotation with position), RM sign set by a single global handedness with no gradient.
- *Purely poloidal field*: EVPA aligned along the jet axis everywhere, negligible transverse RM gradient.
- *Null/tangled field* (baseline): polarization fraction suppressed by a disorder parameter, RM and EVPA drawn from a random (zero-mean, no systematic gradient) distribution — this is the null hypothesis against which the ordered-field models are tested.

Each model has 2–4 free parameters (e.g., pitch angle, field normalization, overall EVPA offset/position-angle zero-point, disorder fraction for the null model). Code all four as Python functions in a shared module (`field_models.py`) taking position along the jet and returning predicted (m, EVPA, RM).

**3. Fitting each model to the compiled data**

- Fit each model to the digitized EVPA(s) and RM(s) datasets using `scipy.optimize.least_squares` (or `lmfit` for convenient parameter bounds/reporting) with the digitization/reported uncertainties as weights.
- Because the sample size is small (tens of points) and the models are low-dimensional, additionally run each fit through an MCMC sampler (`emcee`) with weakly informative, physically motivated priors (e.g., pitch angle bounded to 0–90°, disorder fraction bounded to [0,1]) to obtain full posterior parameter distributions and marginalized 1σ/2σ confidence intervals rather than relying solely on point estimates.
- Fit RM(s) and EVPA(s) either jointly (shared field-geometry parameters, since both observables derive from the same field model) or in a clearly labeled two-step approach if a joint likelihood proves numerically unstable — decide based on how well-constrained the joint fit turns out to be, and report whichever choice is used.

**4. Quantitative model comparison**

- Compute χ² and reduced χ² for each best-fit model against the data.
- Compute AIC and BIC for each model, using the number of free parameters and data points, to penalize the more flexible helical model appropriately relative to the simpler toroidal/poloidal/null alternatives.
- Report ΔAIC and ΔBIC relative to the best-performing model, and convert to Akaike weights to give an interpretable relative-support statistic across all four models.
- Because N is small, cross-check the ranking with leave-one-out cross-validation (refit excluding each point in turn, measure predictive scatter) to verify the preferred model isn't driven by one or two influential points — report this as a robustness diagnostic on the same ranking, not as a separate analysis.
- Present the final comparison as a single summary table (model, χ², reduced χ², ΔAIC, ΔBIC, Akaike weight) plus a figure overlaying the four best-fit curves on the digitized RM(s) and EVPA(s) data points with their error bars — this table and figure are the central quantitative result of the thesis, replacing the original paper's qualitative "the RM gradient suggests a helical field" statement with an explicit statistical preference.

**5. Secondary consistency check using VAPOLA**

- Compile, in the same spreadsheet format as Step 1, any publicly reported VAPOLA core-region polarization fraction, EVPA, and RM values for M87 across its available epochs/bands (again transcribed from tables or digitized from figures, with the same double-digitization uncertainty procedure).
- Do not refit the field models to these points. Instead, take the field-geometry sign/handedness and pitch-angle range favored by the Step 4 jet-scale fit and check, epoch by epoch, whether the VAPOLA core EVPA/RM sign is compatible with that same convention (e.g., is the core RM sign consistent with the handedness the jet fit prefers, within the VAPOLA-reported uncertainties?).
- Present this strictly as a small-N, epoch-resolved compatibility table (consistent / inconsistent / inconclusive per epoch), explicitly flagged in the thesis text as a secondary, non-definitive check rather than a joint model fit, since VAPOLA's core-region physics (opacity, time variability) is not itself modeled by the same static jet formulas.

**6. Tools and deliverables**

- Software: Python (numpy, scipy, pandas, matplotlib, astropy for unit/coordinate handling, emcee for posterior sampling, lmfit as an alternative fitting front end), WebPlotDigitizer for figure extraction, and a version-controlled repository containing the digitized-data spreadsheet, `field_models.py`, fitting/analysis notebooks, and all generated figures/tables.
- Deliverables: (1) the fully documented digitized-measurement table with provenance for every value; (2) the four implemented analytic field models with derivations included in an appendix; (3) best-fit parameters and posterior distributions for each model; (4) the χ²/AIC/BIC/Akaike-weight model-comparison table and overlay figure; (5) the leave-one-out robustness check; (6) the VAPOLA epoch-by-epoch consistency table. Together these constitute a complete, self-contained quantitative test of the helical-field interpretation of M87's jet, built entirely from already-published numbers.
