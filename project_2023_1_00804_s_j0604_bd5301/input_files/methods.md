# Methods

## 0. Software environment and bookkeeping

Everything below runs in CASA (the version matching the delivered pipeline, so that the archive's calibration scripts execute without version drift), with the analysisUtils package for metadata and atmospheric-transmission inspection, and with numpy/scipy/astropy/matplotlib for the post-extraction analysis. Do the imaging in CASA and nothing else; do the spectral analysis in Python and nothing else. Keep two artifacts from day one: a git repository holding every script, and a single machine-readable master table (one row per target, one column per measured or recorded quantity) that every figure and every number in the thesis is generated from. No number goes into the text by hand. These reduction scripts are working notes — they need to run start-to-finish, not be beautiful.

## 1. Week one: inventory and metadata audit of the delivery

Before any imaging, establish exactly what is in hand for program 2023.1.00804.S.

**1a. Count the delivered, QA2-passed targets.** Go through the delivery directory structure and the pipeline weblogs and produce the definitive list of targets with delivered, QA2-passed data. That number, not the 40 in the proposal, is the sample. Record any target that appears in the proposal but has no delivered data, and mark it as such — the sample definition must be auditable.

**1b. Read the observing setup off the measurement sets themselves.** For each MS, run `listobs` and dump the `SPECTRAL_WINDOW`, `SOURCE`, and `FIELD` subtables. From these you take three things per target: (i) the sky-frequency coverage, channel width, and number of channels of every spectral window; (ii) the rest frequency carried in the delivered setup for that target's H₂O⁺ tuning (the `REST_FREQUENCY` entry associated with the science source); and (iii) the per-target redshift or systemic velocity recorded in the same delivered metadata. These are PI-supplied values and you treat them as approximate throughout. In your master table, label the tabulated line frequency explicitly as *rest-frame as recorded in the delivery*, and label every frequency you derive from it by redshifting it into the observed band as *observed-frame, traceable to the recorded redshift*. If the delivery does not state which frame a recorded value is in, write "frame not stated in delivery" in that cell and say so in the thesis. Do not import a frequency from an external spectroscopic database, and do not silently adopt one frame when the delivery is ambiguous — the entire analysis is designed so that this level of frequency provenance is sufficient, because every quantity you report is either an integral over a wide fixed window or a width, never a centroid and never a velocity shift.

**1c. Answer the OH⁺ question and then stop thinking about it.** For each target, check whether an OH⁺ transition, at the rest frequency recorded in that same delivered setup and redshifted by the recorded redshift, falls inside a delivered spectral window. Record yes/no per target. If yes for some sightlines, those get the identical measurement procedure of §5 and land in an appendix table; if no, nothing in the thesis changes. Do not construct any N(H₂O⁺)/N(OH⁺) ratio.

**1d. Flag bad spectral placement now, not later.** For each target, compute where the fixed analysis window (§4) lands within its spectral window. Exclude a sightline if the window falls within the outermost ~5% of channels at either spw edge (where the bandpass response and its calibration uncertainty rise steeply), or if it overlaps a strong atmospheric feature. Judge the latter from the delivery itself: the ATM transmission curve for the actual observing conditions (via analysisUtils) plus the Tsys spectra in the pipeline weblog. Record each exclusion with its reason in the master table. These exclusions are made before any line measurement is inspected.

## 2. Calibration and continuum imaging

**2a. Restore the delivered calibration.** Run the archive's `scriptForPI.py` (or the pipeline restore task) to regenerate the calibrated MSs. Do not re-derive the calibration. Then use `mstransform`/`split` to produce a science-target-only, time-averaged MS per source, keeping full spectral resolution — this keeps the working data volume manageable for a year-long project.

**2b. Define line-free channels.** For each spw, mask the fixed H₂O⁺ analysis window (and the OH⁺ window where applicable) and treat the remainder as continuum. Inspect the vector-averaged spectrum per spw to catch any additional unexpected feature and extend the mask if needed, recording the change.

**2c. Image the continuum.** Per target, per spw and also for the aggregate of all line-free channels, run `tclean` in `mfs` mode with `nterms=1`, Briggs weighting at `robust=0.5`, cleaning to a threshold of ~2× the dirty-image rms with a hand-drawn or `auto-multithresh` mask, and apply primary-beam correction. Use the same weighting and the same cell/imsize convention (≥5 cells per synthesized beam minor axis) for every target so the photometry is uniform.

**2d. Photometry with one documented convention.** Measure the continuum flux density with `imfit`, fitting a single Gaussian component on the pb-corrected image, and record both the peak intensity and the integrated flux density along with the fitted size and whether the source is resolved. Cross-check against an aperture measurement in a fixed aperture. Take the noise σ_cont from `imstat` in a signal-free region of the non-pb-corrected image, and quote the continuum SNR as peak/σ_cont. Fix one convention — peak-based SNR — as *the* ranking statistic and use it everywhere; report the aperture cross-check in the table as a consistency column.

**2e. Rank and cut, then freeze.** Sort all non-excluded targets by continuum SNR, write that ranking into the master table, choose the cut that defines the ~8–10-source strong-continuum primary subset, and record the cut value. Do this *before* you look at a single H₂O⁺ profile. Date-stamp the frozen ranking file in git so it is provable that the subset was not chosen after seeing the lines.

## 3. Spectral extraction

For each target, extract the spectrum at the continuum peak pixel from an image cube made with `tclean` in `cube` mode over the spw containing the analysis window, using the same weighting as the continuum imaging. For any source resolved in the continuum fit of step 2d, also extract a spectrum integrated over the continuum-emitting aperture and carry both versions through the analysis; report the peak-pixel version as primary and the aperture version as a consistency check, since the aperture version dilutes absorption if the absorbing layer does not cover the full continuum extent.

Bin channels to a common velocity resolution across the sample — pick the coarsest native resolution among the primary subset, likely a few tens of km/s, and bin everything to it. Percent-level absorption does not need fine channels, and binning is what makes the sightlines comparable.

## 4. Continuum normalization and the velocity axis

**4a. Build the velocity axis from the delivery.** Convert observed frequency to velocity using the recorded rest frequency and the recorded redshift for that target, with the frame labels of §1b carried through. Define one fixed, generously wide analysis window — I suggest ±1500 km/s about v = 0 — and use the *identical* window for every sightline, every upper limit, and every injection test. Never tune the window per source.

**4b. Fit and divide.** Fit a low-order polynomial (order 0 or 1 by default; go to order 2 only if the residuals demand it, and record where you did) to the line-free channels of the spw, excluding the analysis window, and divide the spectrum by it to get the continuum-normalized profile I(v)/I_c.

**4c. Propagate the continuum-fit uncertainty, not just thermal noise.** Refit the continuum many times (≥200) with the line-free region jackknifed — randomly dropping contiguous blocks of line-free channels and, where applicable, varying the polynomial order — and take the resulting spread in I_c(v) as the continuum-placement error, added in quadrature to the thermal noise at every velocity. This term will dominate at high continuum SNR and it is what actually sets your detection floor.

**4d. Establish the noise floor empirically.** Baseline ripple, not raw sensitivity, is the realistic failure mode here. Slide the identical fixed window to many line-free velocity offsets across the same spw, measure the integrated optical depth in each (§5b), and take the standard deviation of that distribution as σ(∫τ dv) for the sightline. This empirical σ — not a propagated per-channel estimate — is what defines your 3σ limits and your significance thresholds. Do this per target and record it.

## 5. Per-sightline characterization

All of the following use the fixed window of §4a and a single code path shared with §6.

**5a. Classification.** Compute the significance of the window-integrated signal against the empirical σ from §4d. Declare *absorption* if the integrated signal is negative at ≥3σ, *emission* if positive at ≥3σ, and *non-detection* otherwise. Declare *P-Cygni* only if the window contains both a ≥3σ negative and a ≥3σ positive contiguous segment adjacent in velocity; because the redshift is approximate, describe the geometry as "adjacent negative and positive segments" and do not assert which side is blueshifted relative to systemic. Emission against a bright continuum is a legitimate physical outcome for a ground-state hydride and is reported as a detection, not as a failure.

**5b. Integrated optical depth.** With covering factor C_f as a free parameter, the normalized profile is I(v)/I_c = 1 − C_f(1 − e^{−τ(v)}). Adopt C_f = 1 as the fiducial, giving τ(v) = −ln[I(v)/I_c], and integrate over the fixed window to get ∫τ dv in km/s. Because C_f = 1 is the maximal-covering assumption, every optical depth and every column derived from it is a strict lower limit; state that each time. Recompute the full table once with one alternative value (C_f = 0.5) purely to display the direction and magnitude of the shift. Where the profile drives I/I_c to or below zero within the noise, do not take the log — integrate in the linear (1 − I/I_c) domain and flag the channel, since that is the regime where the optically-thin equivalence breaks.

**5c. Upper limits.** For non-detections, report a 3σ upper limit on |∫τ dv| computed over the *identical* window using the empirical σ from §4d. Never widen or narrow the window to improve a limit.

**5d. Equivalent width.** Report W = ∫(1 − I/I_c) dv in km/s over the same window. This is the most assumption-free number you will produce; quote it alongside ∫τ everywhere.

**5e. Velocity extent Δv₉₀.** Form the cumulative integral of τ(v) across the window and define Δv₉₀ as the width of the contiguous interval running from the 5% to the 95% point of the total. Estimate its uncertainty by Monte Carlo: perturb the normalized spectrum by its full error array (thermal + continuum-placement) many times and re-run the same estimator. Every time you quote a Δv₉₀ in the thesis, state inline that it is formally an upper bound on the intrinsic kinematic extent because the hyperfine structure of the transition contributes width. State also, once and clearly, why differences in Δv₉₀ between sightlines are nonetheless meaningful: the hyperfine pattern is identical in every source, so its contribution is common-mode.

**5f. Column density.** Convert the fiducial C_f = 1 integrated optical depth to a column density via the standard ground-state absorption relation, N = 𝒞 · ∫τ dv, assuming that essentially all of the population resides in the ground state (state this assumption explicitly). Tabulate the constant 𝒞 and every molecular-data input that goes into it — the Einstein A coefficient, the statistical weights, and the rest-frame line frequency, which is the *approximate, as-recorded* value from §1b — as an explicit, separately-listed row in the table, with the source of each adopted value named. Reporting N in the form 𝒞 · ∫τ dv means the column can be rescaled by anyone who adopts different molecular data, and it keeps ∫τ dv and W as the primary, conversion-independent results.

## 6. Injection–recovery completeness

This is what turns a raw count of detections into a detection rate, so build it as a first-class part of the pipeline rather than an afterthought.

Into each target's *real* normalized spectrum, inject synthetic absorption profiles of known integrated optical depth and known Δv₉₀ on a grid — ∫τ dv spanning roughly a decade below to a decade above your typical 3σ limit, Δv₉₀ spanning ~100 to ~1500 km/s — at randomized velocity offsets within the window, using a simple Gaussian (and, as a shape check, a top-hat) profile. Run each realization through the *identical* code path used in §5, including the continuum refit, and record whether it was recovered at ≥3σ and what ∫τ dv and Δv₉₀ came back. Run of order a few hundred realizations per grid cell per target.

This yields two products. First, the per-target and ensemble completeness function — recovered fraction as a function of true ∫τ dv and true Δv₉₀ — which corrects the detection rate. Second, the measurement bias on Δv₉₀ itself: the mean and scatter of (recovered − true) Δv₉₀ as a function of continuum brightness and input width. Quote every measured Δv₉₀ with this bias characterized.

## 7. The headline product: detection rate versus depth threshold

Do not report a single detection fraction. Report a curve: for a grid of integrated-optical-depth thresholds τ_thr, plot the fraction of sightlines with detected H₂O⁺ having ∫τ dv ≥ τ_thr, divided by the injection–recovery completeness at that τ_thr, with binomial (Wilson or beta) confidence intervals appropriate to small N. Overplot the per-sightline 3σ limits from §5c as tick marks along the threshold axis, so a reader sees immediately which part of the curve is constrained by real sensitivity and which is extrapolation.

Do not plot or fit any correlation between the H₂O⁺ measurements and observed continuum flux density. Across z = 2–5 that quantity mixes luminosity distance, the dust SED K-correction, dust temperature, and possible magnification, so a trend against it would carry no physical meaning. Continuum brightness enters this thesis in exactly one role — the sensitivity axis of the measurement — and the plots should make that role visually explicit.

## 8. The stack

One stack, of every accessible normalized spectrum, including the sightlines too faint for individual measurement.

Resample all normalized spectra onto the common velocity grid defined in §4a (linear interpolation is fine at the binned resolution; do not smooth). Weight each sightline by the inverse variance of its normalized spectrum — which is the continuum-SNR-squared weighting in practice — and average. Report from the stack: the ensemble-average profile, its mean depth, its equivalent width, its Δv₉₀ measured with the identical §5e estimator, and, if the stack is not detected at ≥3σ, the stacked 3σ upper limit on ∫τ dv, which is itself the quantitative result.

Run three checks on the stack and report all three: (i) jackknife — split the sample in half by continuum SNR and by observation date and confirm the two halves agree within their errors; (ii) a null stack in which each spectrum is shifted by a large random velocity offset before combining, which must be consistent with zero; (iii) a bootstrap over sightlines for the uncertainty on the stacked depth and width, since with small N the sightline-to-sightline scatter, not the per-spectrum noise, dominates.

## 9. Products to assemble

Build these directly from the master table so they regenerate on a single command:

- **(a)** The detection-rate-versus-threshold figure with per-sightline 3σ limits and the injection–recovery completeness correction.
- **(b)** The ∫τ dv, equivalent width, and Δv₉₀ distributions across the strong-continuum subset, with the hyperfine upper-bound caveat printed in the caption and stated at each mention in the text.
- **(c)** The spectral atlas: every analyzed sightline's continuum-normalized H₂O⁺ region on the common velocity axis, one panel per source, with the fixed window marked, the ±1σ envelope shaded, and the §5a classification labeled in the panel.
- **(d)** The single stacked profile with its jackknife and null-stack panels.
- **(e)** *Stated as secondary:* the uniform continuum photometry table from §2, flagged in the text as a byproduct useful to the group and not a science claim of this thesis.
- **(f)** *Appendix, contingent on §1c:* the identical window-integrated OH⁺ measurements for whichever sightlines have OH⁺ in a delivered spectral window.
- The master table itself, published as a machine-readable table, with the frame labels of §1b, the exclusion reasons of §1d, the frozen SNR ranking and cut of §2e, and the molecular-data constants of §5f all carried as explicit columns.

## 10. Suggested sequencing

Weeks 1–2: §1, the full metadata audit, including the OH⁺ answer and the exclusion list. Weeks 3–8: §2, calibration restore and uniform continuum imaging and photometry across the whole delivered sample; freeze the ranking at the end of this block. Weeks 9–14: §3–§4 on the primary subset, with particular care on the empirical noise floor. Weeks 15–20: §5, the per-sightline measurements. Weeks 21–26: §6 injection–recovery and §7 the detection-rate curve. Weeks 27–30: §8, the stack and its null tests. Remainder: §9 and writing. If the schedule compresses, the stack (§8) and the appendix (§9f) are what shrink; §6 does not, because without completeness the headline result has no meaning.
