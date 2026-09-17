## 0. The one sentence that governs everything

Before you touch a single dataset, fix in your head what this thesis measures: **the beam flux density at the catalog nuclear position of each target, in the ACA Band 6 continuum.** The ACA cannot separate a nucleus from its immediate circumnuclear surroundings, so that is the observable — not "the nuclear flux." It is a perfectly well-defined quantity with real detections and real upper limits, and it bounds the nuclear quantity in exactly one direction: nuclear flux ≤ beam flux. You will state that inequality in the abstract, carry the beam flux consistently through photometry, completeness, and statistics, and apply the inequality once, in words, at the end. You will not produce a second set of "nucleus-corrected" numbers from an assumed subtraction the data cannot constrain.

A second piece of bookkeeping, also fixed now. The project description quotes "230 GHz" without saying whether that figure is rest-frame or observed-frame. Treat it as a **nominal Band 6 label only**, say so explicitly in the thesis, and never quote it as the frequency of a measurement. Every measurement gets its own effective observed sky frequency, read from the SPW definitions and image headers of that field. The same discipline applies to the ring-size tiers (>8 and >2 microarcsec are *predicted* ring diameters from the proposal's selection, not measured ones), to the ~10 mJy promotion threshold, and to the "few 10s of mJy" passive-phased EHT floor — both of the latter are levels quoted by the project, and you report the fraction of the sample clearing them without endorsing them as physical constants.

## 1. Week one: three gating steps, then sign-off

Do these before I approve the sample. They convert the three things that can sink the project from risks into known quantities.

**1.1 Archive query and proprietary audit.** Query the ALMA Science Archive for project code 2023.1.01099.S, field by field, using the archive's TAP/ObsCore interface (`astroquery.alma`, or the web portal export). For every scheduling block, record: member OUS ID, source name and catalog J2000 coordinates, band, release date, and current public/proprietary status. Produce `field_inventory.csv`. The number that matters is *how many fields are released today* — that is your universe. Do not plan against the 803 in the proposal; plan against the released count.

**1.2 Metadata request to the PI team — bonus, not dependency.** Write to the PI asking for the per-target predicted ring diameters, the SMBHB-candidate flags, and host distances. If they arrive, they buy you a continuous covariate (ring size as a real number) and physical scales in parsecs. If they never arrive, nothing breaks: the primary analysis needs only the tier labels the project description already supplies (>8 vs >2 microarcsec; SMBHB candidate vs single). Write your sample-selection rule so it executes on tier labels alone, and treat any richer metadata as an add-on analysis.

**1.3 Disk audit.** Pipeline continuum images (FITS, `.image`, `.pb`, `.residual`) are cheap. Calibrated measurement sets for the uv-plane cross-check are not — budget **~5–15 GB per calibrated ACA Band 6 dataset**. Therefore: retrieve in batches of ~25 fields; on arrival, immediately run `split` with channel averaging down to a continuum-only MS (a handful of channels per SPW, enough to preserve the frequency axis for the header record but not the full spectral resolution); delete the full-resolution MS once the split product passes a `listobs` and visibility-count check. Keep the working set to a few hundred GB. Write this as a script (`stage_batch.py`) on day one — you will run it dozens of times.

## 2. Pre-registered sample: ~120 fields, fixed before any flux is looked at

This is the step that protects the result, so it is formal. Write the selection rule into your thesis proposal document, commit it to the repository with a timestamp, and *then* start measuring.

- **Tier A:** every released target drawn from the 68 with predicted ring > 8 microarcsec.
- **Tier B:** a random draw from the released > 2 microarcsec piggyback fields and the 124 SMBHB candidates, sized to bring the total to ~120 and to balance the comparison cells (large-ring vs piggyback; SMBHB candidate vs single). Use `numpy.random.default_rng(seed)` with the **seed written into the proposal document**, so the draw is reproducible and auditable.

Fields beyond ~120 are explicit stretch goals, added only in the final semester if throughput allows, and flagged as post-hoc additions in every table they appear in. Fields that fail QA (Section 3.4) are **reported as failures, not silently replaced** — replacing them would break the pre-registration. This is not all 803 fields and the thesis says so plainly.

## 3. Measurement: one script, run identically on every field

Uniformity is the deliverable. Every bespoke reduction you are tempted to do is a bias you cannot characterize. Write one function, `measure_field(ms, image_products, ra, dec)`, and run it unchanged.

**3.1 Imaging.** Prefer the archive's pipeline continuum products where they exist and pass QA; they are already uniform by construction. Where you must image yourself, use a single fixed `tclean` recipe: `specmode='mfs'`, `deconvolver='mtmfs'` with `nterms=1` (the ACA fractional bandwidth does not warrant more for faint sources), Briggs weighting at `robust=0.5`, a cell size giving ~5 pixels across the minor axis of the synthesized beam, an image size covering the primary beam out to at least the 20% level, and a shallow clean (`niter` a few hundred, `threshold` at ~3× the expected thermal rms) with no interactive masking. Record every parameter to the per-field log. If any field cannot be imaged with the standard recipe, it is a QA failure, not a special case.

**3.2 Header and scale bookkeeping.** For each field, pull and tabulate: the observed sky frequencies and bandwidths of every SPW and the bandwidth-weighted **effective frequency** of the continuum image; the synthesized beam major axis, minor axis, and position angle; the shortest and longest projected baselines actually present in the data; and the **maximum recoverable scale** computed from the shortest baseline at the effective frequency. The ACA's ~9–45 m baselines give you a synthesized beam of order several arcseconds and an MRS of order tens of arcseconds — but do not quote nominal numbers, compute them per field from the data and report those. Where PI-supplied host distances exist, convert both the beam and the MRS to physical scales; where they do not, report angular scales only. This table is what tells the reader precisely what angular scale the beam flux integrates over, and above what scale emission has been resolved out.

**3.3 Photometry — forced, at a fixed position.** For every field, in both planes:

- *Image plane.* Extract the primary-beam-corrected image. At the catalog nuclear J2000 position, fit a single elliptical Gaussian with the shape **fixed to the restoring beam** and the position **fixed to the catalog coordinates** (`imfit` with fixed parameters, or a direct least-squares fit on the pixel grid). The fitted amplitude is the beam flux density. Measure the local rms in an annulus centered on the source, inner radius ~5 beams and outer ~15 beams, with sigma-clipping and with any other catalogued or obviously bright sources masked; use the un-primary-beam-corrected map for the rms and scale it by the primary beam response at the source position, so that the noise estimate is not contaminated by the pb correction's radial gradient. As a diagnostic only, refit allowing the centroid to float within one-third of a beam; record the offset. A large offset flags the field for visual inspection, but the reported number remains the forced measurement at the catalog position.
- *uv plane cross-check.* On the continuum-averaged MS, fit a point source at the catalog position with the position held fixed (`uvmodelfit` with `comptype='P'`, or an equivalent direct fit to the visibilities after phase-shifting the phase center to the catalog coordinates). This bypasses deconvolution entirely.

The two estimates must agree within their joint uncertainties. Plot image-plane against uv-plane flux for the whole sample; the scatter and any offset in that plot is a headline systematics figure in the thesis. Disagreement beyond a pre-set tolerance flags the field for inspection.

**3.4 Detections, limits, and the uncertainty budget.** Adopt a single detection criterion, fixed in advance — I recommend **SNR ≥ 5** on the forced image-plane amplitude — and apply it identically everywhere. For detections, the uncertainty is the quadrature sum of (i) the thermal/fit uncertainty from the local rms and the fit covariance and (ii) the **absolute flux-calibration systematic**, taken from the ALMA Technical Handbook value for Band 6 in the relevant cycle (of order 5–10%; adopt one number, state it, apply it uniformly, and note that it is a systematic common to a field's whole calibration and therefore does *not* average down across a scheduling block). Report the two terms separately in the machine-readable table so the reader can recombine them. For non-detections, report an upper limit at a stated confidence level — 3× the local rms, with the confidence level and the multiplier written explicitly — never a "measured" flux with a large error bar.

**QA gates** (all automatic, all logged): `listobs` sanity, presence of the standard calibrators, image rms within a factor of a few of the sensitivity implied by the on-source time, no severe residual sidelobe structure near the nuclear position, catalog position inside the primary beam FWHM, and image-plane/uv-plane agreement. Fields failing any gate are tabulated as failures with the reason given.

## 4. Completeness: analytic, then validated by injection–recovery

Because photometry is *forced at a known position*, you do not have a source-finding problem, and the completeness function collapses to something you can write down. The recovered amplitude at a fixed position is Gaussian about the true flux with width equal to the local rms, so the probability of a field with rms σ yielding a detection of a source of flux S is simply the Gaussian tail above your threshold: C(S | σ) = Φ((S − kσ)/σ) for a k-sigma criterion. Derive this in the thesis, in one short subsection, from the fit statistics.

Then check it, because the derivation assumes the residual maps are noise-like and the fit is unbiased:

- Select **15–20 representative fields** spanning the observed range of rms, synthesized beam size and elongation, and residual-map structure (include the ugliest residuals you have — that is the point).
- Inject point sources **into the visibilities** of the continuum MS at a grid of flux levels bracketing the threshold (say 0.5–10× the local 3σ), at positions offset from the true nucleus but within the inner primary beam, one or a few injections per realization so they do not interact. Use a component list plus `ft` to populate `MODEL_DATA` and add it to `DATA` in a scratch copy of the MS.
- Re-image with the *identical* `tclean` recipe and re-run the *identical* forced photometry at the injected position.
- From the recovery fraction as a function of flux/rms, measure the empirical completeness curve; from the recovered-minus-injected distribution, measure the **flux-recovery bias and scatter**.

If the empirical curves match the analytic form within their uncertainties, adopt the analytic form sample-wide — that is the whole point of doing it this way, and it keeps you to hundreds of `tclean` calls rather than tens of thousands. If they do not match, characterize the discrepancy (is it confined to fields with poor residuals? does the bias scale with beam elongation?), and extend the injections only into the region of parameter space where the analytic form fails. Document whichever branch you took.

## 5. Censored statistics on the beam flux

Every statistical statement is about the beam flux distribution, using detections and upper limits together.

- **Distribution.** Upper limits are *left*-censored data. Construct the Kaplan–Meier estimator of the beam flux distribution after the standard sign-flip that maps left-censoring onto the right-censored form the standard estimators expect (`lifelines`, `scikit-survival`, or an ASURV-equivalent implementation you verify against a hand-worked example). In parallel, fit a censored maximum-likelihood parametric model — a log-normal in flux is the natural first choice — using the per-field completeness curve as the likelihood's censoring model, so that fields of different depth are weighted correctly. Report both; agreement between the nonparametric and parametric results is your robustness check.
- **Threshold fractions.** From the censored distribution, report the fraction of the sample above the project's **~10 mJy** 12 m/VLBA promotion level and above the **few-tens-of-mJy** level quoted as the passive-phased EHT floor, each with a confidence interval (bootstrap over fields for the KM estimate; profile likelihood for the parametric fit). Then, in a single sentence, apply the inequality: because nuclear flux ≤ beam flux, these fractions are **upper bounds** on the true nuclear rates.

## 6. The primary comparison, with power computed first

Two contrasts, both pre-specified:

1. **Tier A (predicted ring > 8 microarcsec) vs Tier B (piggyback > 2 microarcsec).**
2. **SMBHB candidates vs single SMBHs.**

Test each with a two-sample censored test on the beam flux distributions. Use the **Peto–Prentice weighted logrank** as the primary statistic, because the two cells will not have identical censoring patterns and that variant is the more robust choice under unequal censoring; report the plain logrank and Gehan statistics alongside as a sensitivity check. In addition, report the simple binary detection-rate contrast above each fixed threshold with a Fisher exact test and its confidence interval, so there is one number a reader can grasp without survival theory. If the PI metadata arrives, add a censored regression of beam flux on predicted ring diameter as a continuous covariate — as a secondary, clearly labelled analysis.

**Compute the power before you look at the answer.** Using the actual per-field rms values from `field_inventory.csv` and the analytic completeness curves, simulate many realizations under a range of assumed true beam flux distributions and rate differences, run the full test pipeline on each, and determine the **minimum detectable rate difference** at 80% power for your achieved sample size. Put that number in the proposal, before unblinding. Then, whatever the data say, you have a quantitative statement: either a measured difference, or an upper limit on any difference that is meaningful because you knew in advance what you could have detected.

## 7. Reproducibility and deliverables

Everything runs from a version-controlled repository: `stage_batch.py`, `measure_field.py`, `inject_recover.py`, `censored_stats.py`, one driver notebook, and a `config.yaml` holding every threshold, weighting, and seed in one place so no constant is buried in code. Every field writes a JSON log with software versions, `tclean` parameters, header values, fit outputs, and QA verdicts.

What you hand in:

(a) A machine-readable table of nominal-Band-6, nuclear-position **beam flux densities and upper limits** for ~120 fields, with per-target observed effective frequency, bandwidth, synthesized beam, maximum recoverable scale (angular, plus physical where distances are available), separated thermal and calibration uncertainties, and QA status.
(b) The analytic completeness curves and their injection–recovery validation on the 15–20 field subsample, including the flux-recovery bias and scatter.
(c) The censored beam flux distribution and the detection rates above ~10 mJy and above the few-tens-of-mJy level, with confidence intervals, and the nuclear-flux bound stated once.
(d) The Tier A vs Tier B and SMBHB vs single contrasts with confidence intervals and the pre-computed minimum detectable difference.
(e) The pipeline itself, documented and ready to run unchanged on the remaining released fields.

Include the ALMA acknowledgement for ADS/JAO.ALMA#2023.1.01099.S verbatim, and the standard NRAO acknowledgement, in every document that leaves the group.
