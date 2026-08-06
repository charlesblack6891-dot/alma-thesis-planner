> **Caution: this idea did not pass all of Stage 5's own tractability checks.** Review the failed item(s) below before treating this as a ready-to-execute thesis plan.
> - 3. NO -- A domain expert in jet polarimetry would likely object that hand-digitized values from a single paper's figures carry unquantified measurement error too large to support a formally rigorous chi-square/AIC/BIC discrimination between helical, toroidal, and poloidal models, making the proposed statistical comparison more cosmetic than robust, and the project never touches the actual assigned ALMA dataset at all.

# Quantitative Model Comparison of Magnetic-Field Geometries in the M87 Jet Using Published ALMA Polarization Values

## Abstract

The assigned ALMA dataset (2025.1.00830.V) is proprietary until mid-2027 and cannot anchor a thesis, but two already-public ALMA-derived resources bear on the same physical question its inferred goal touches: the state and structure of the magnetic field in M87's core/jet-base region. Aviles Contreras et al. (A&A 699, A265, 2025) report Band 7 (345 GHz) linear polarization fractions (1–17%) and a rotation-measure (RM) gradient along the M87 jet, interpreted qualitatively as evidence of a helical field; the VAPOLA survey provides complementary multi-epoch, multi-band core polarization values. This thesis uses only these already-published numbers — polarization fractions, EVPAs, and RM values as reported in tables/figures — to fit four analytic toy magnetic-field models (helical, purely toroidal, purely poloidal, null/tangled) to the compiled M87 jet data, and performs a quantitative model-comparison (χ², AIC/BIC, Akaike weights) to test how strongly the data favor the helical interpretation over simpler alternatives — a test the original paper does not itself perform. A secondary, explicitly small-N check compares VAPOLA core-region polarization sign/magnitude against the field-geometry convention favored by the jet-scale fit. No raw visibility, calibration, or imaging work is involved; the project is bounded to literature-value compilation and standard analytic/statistical modeling.

## Work Plan

**1. Data compilation.** Build a version-controlled spreadsheet of every polarization measurement in A&A 699, A265: fractional linear polarization *m*, EVPA (χ), Stokes I/Q/U, RM, and uncertainties, tagged by deprojected distance/position angle and location (core, jet base, extended jet). Transcribe tabulated values directly; digitize graphical values with WebPlotDigitizer, calibrated against axis ticks, each panel digitized twice independently to estimate uncertainty (adopting the larger of digitization scatter or stated error bars). Record source figure/table/page for auditability. Expect ~15–40 usable points.

**2. Candidate field models.** Implement in Python (`field_models.py`) closed-form EVPA(s)/RM(s) predictions for four geometries using standard jet-polarization formulas (Blandford & Königl 1979; Blandford 1993; Lyutikov, Pariev & Gabuzda 2005; Pushkarev/Gabuzda RM sign-reversal tests): helical (B_φ∝1/r, B_z∝1/r², pitch angle), purely toroidal (no EVPA rotation, single-handedness RM), purely poloidal (EVPA along jet axis, negligible RM gradient), and null/tangled (random RM/EVPA, disorder parameter) as baseline. Each model has 2–4 free parameters.

**3. Fitting.** Fit each model to digitized EVPA(s)/RM(s) via `scipy.optimize.least_squares` (or `lmfit`), weighted by uncertainties, then re-fit with `emcee` MCMC using weakly informative priors (e.g., pitch angle 0–90°, disorder fraction [0,1]) to obtain posteriors and confidence intervals. Fit RM and EVPA jointly where numerically stable, else a labeled two-step approach.

**4. Model comparison (central result).** Compute χ²/reduced χ², AIC, BIC, ΔAIC/ΔBIC, and Akaike weights per model. Cross-check ranking robustness via leave-one-out cross-validation. Deliver a summary table (model, χ², reduced χ², ΔAIC, ΔBIC, Akaike weight) and a figure overlaying best-fit curves on the digitized RM(s)/EVPA(s) data with error bars — replacing the source paper's qualitative helical-field claim with an explicit statistical preference.

**5. Secondary VAPOLA consistency check.** Compile VAPOLA core-region polarization/EVPA/RM values (same spreadsheet/digitization protocol). Without refitting, check epoch-by-epoch whether core RM sign/magnitude is compatible with the handedness/pitch-angle range favored by the jet-scale fit; present as a labeled compatibility table (consistent/inconsistent/inconclusive), flagged as supplementary.

**Tools & deliverables:** Python (numpy, scipy, pandas, matplotlib, astropy, emcee, lmfit), WebPlotDigitizer, Git repository. Deliverables: documented digitized-measurement table with provenance; four implemented field models with derivations (appendix); best-fit parameters and posteriors; χ²/AIC/BIC/Akaike-weight comparison table and overlay figure; leave-one-out robustness check; VAPOLA epoch-by-epoch consistency table.

## Background Reading

- C. Goddi et al. (2025), "First polarization study of the M87 jet and active galactic nuclei at submillimeter wavelengths with ALMA"
- C. Goddi et al. (2021), "Polarimetric Properties of Event Horizon Telescope Targets from ALMA"
- Dhanya G. Nair et al. (2024), "Demographics of black holes at <100 Rg scales: accretion flows, jets, and shadows"
