# Testing for Wind Clumping in an OB-Type Star via ALMA Multi-Band Spectral Index

## Abstract

Massive, hot stars drive strong winds that regulate their mass loss, but current mass-loss-rate estimates may be wrong by up to a factor of ten because it is unknown whether these winds are smooth or structured into dense clumps. This thesis tests wind clumping in one OB-type star from this project's ALMA observations by measuring the mm/sub-mm continuum spectral index (α, from S_ν ∝ ν^α) across two or three observed bands and comparing it to the theoretical benchmark of α≈0.6 expected for free-free emission from a smooth, spherically symmetric, constant-velocity wind (Wright & Barlow 1975 / Panagia & Felli 1975 relation, external to this proposal). The full multi-wavelength, Non-LTE wind modeling described in the parent proposal is out of scope; this project delivers a single-star, single-model qualitative classification — smooth vs. clumped — as its primary result, with an absolute mass-loss rate as a contingent stretch goal only if literature stellar parameters (distance, terminal velocity, radius) can be found. Because the proposal's requested bands are not yet confirmed as delivered at usable sensitivity, feasibility must be verified against the actual calibrated data before analysis proceeds.

## Work Plan

**Step 1 — Feasibility gate (first task).** Survey delivered, calibrated continuum images/visibilities for this project. For each OB star, measure continuum SNR (peak flux / local rms) per band. Retain only stars with SNR ≥ 10 in ≥2 bands. If none qualify, pivot to a different ALMA project — no archival flux-point fallback, since no external catalog is named and OB-wind emission varies intrinsically on month–year timescales.

**Step 2 — Target and band selection.** Among qualifying stars, choose the one with the cleanest field (minimal contamination, unresolved structure) and the most qualifying bands. Note whether retained bands are simultaneous or time-separated, flagging non-simultaneous cases as potentially confounded by intrinsic variability.

**Step 3 — Flux density measurement.** Measure flux density in each retained band from calibrated CASA images via point-source fitting (2D Gaussian/delta-function fit convolved with the beam, using `imfit`) as primary method, cross-checked with beam-sized aperture photometry and local background subtraction. Record uncertainties combining image rms and absolute flux calibration error (~5–10%).

**Step 4 — Spectral index determination.** Using only this project's own band fluxes (no archival mixing), fit S_ν ∝ ν^α via linear regression in log(S_ν) vs. log(ν), propagating flux uncertainties into α's uncertainty (or a direct two-point slope if only two bands qualify). Report observed-frame band frequencies as delivered.

**Step 5 — Model comparison and classification (primary deliverable).** Compare measured α (with uncertainty) to the α≈0.6 smooth-wind benchmark, explicitly labeled as an external idealized value. Classify as consistent with smooth-wind, or significantly flatter/steeper (state direction and magnitude in uncertainty units) as expected for radial clumping. Discuss confounds — non-spherical geometry, non-constant terminal velocity, possible band non-simultaneity — as alternative explanations that cannot be excluded.

**Step 6 — Optional stretch goal.** If literature values for distance, terminal velocity, and radius are found, propagate α through the standard radio mass-loss-rate/clumping-factor formalism (Wright & Barlow / Panagia & Felli type relation) to estimate an approximate mass-loss rate and clumping factor, with uncertainties from both α and adopted parameters. Label this result as contingent and lower-confidence than Step 5.

**Anticipated key results/plots:**
- SNR table per target star and band (feasibility check).
- Calibrated continuum image(s) of the chosen target with fitted source position/size overlaid.
- Flux density vs. frequency plot (log–log) with fitted α and error bars.
- Classification summary comparing measured α to the α≈0.6 benchmark, with uncertainty bounds.
- (Stretch) Mass-loss rate and clumping factor estimate with propagated uncertainty range.

## Background Reading

No citation list is available: the literature check found no published paper associated with this project code or target, and the project description contains only standard ALMA boilerplate rather than a bibliography. The theoretical benchmark relation referenced in the Work Plan (spectral index α≈0.6 for smooth free-free wind emission, and the associated mass-loss-rate formalism) is commonly attributed in the field to Wright & Barlow (1975) and Panagia & Felli (1975); these are noted here as standard background context, not as items independently confirmed by the literature search.
