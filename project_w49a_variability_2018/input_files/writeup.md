# Deblending the Crowded Core: A Multi-Component Photometry Reanalysis of W49A's Confused UC/HC HII Regions Across the 1994–2015 VLA Epochs

## Abstract

De Pree et al. (2018) reported significant 3.6 cm flux density variability at one source (G2) in the massive star-forming region W49A, comparing archival VLA B-configuration images from 1994 and 2015. That analysis relied on simple single-component flux measurements, but W49A's densest core (the B/C/D/G clump) contains several UC/HC HII sources close enough at 0.8″ resolution to blend. This thesis addresses a bounded methods question rather than repeating a full-catalog variability census: how much does source blending bias single-component flux measurements in this crowded subfield, and does rigorous multi-component deblending change any source's apparent variability status, including G2's own? Using the same archival, flux-calibrated 1994 and 2015 3.6 cm images, the student will identify the confused subfield, reproduce baseline single-component photometry as a validation check against the published numbers, apply simultaneous multi-component 2D Gaussian fitting to the confused sources only, quantify the resulting bias, and recompute epoch-to-epoch variability significance with corrected fluxes. The deliverable is a quantified methods correction, scoped to a handful of confused sources and two existing archival epochs, using a named, learnable CASA workflow.

## Work Plan

**Phase 0 (1–2 days):** Pull the full De Pree et al. (2018) paper and online tables; extract the published single-component flux census, any explicit blending/confusion flags (historically the B/C/D/G clumps), and the exact imaging parameters (beam, PA, pixel scale, weighting, self-cal). Tabulate as ground truth and starting candidate list.

**Phase 1:** Obtain the calibrated 1994 and 2015 3.6 cm images (or visibilities) from the NRAO archive. If starting from visibilities, image with CASA `tclean` matching the paper's beam/weighting. Align epochs with `imregrid`, verify using isolated point sources, and measure noise floors with `imstat`.

**Phase 2:** Overlay the source catalog on both epochs in CARTA/DS9; measure each source's separation to its nearest neighbor in beam widths. Sources within ~1–1.5 beam FWHM, or with merging contours, form the "confused" list; the rest are "isolated."

**Phase 3 (validation checkpoint):** Run CASA `imfit` with a single 2D Gaussian on every source, both epochs, combining fit, RMS, and calibration errors in quadrature. Confirm G2's measurements reproduce the paper's quoted 71±4→57±3 mJy/beam peak and 0.109±0.011→0.067±0.007 Jy integrated values before proceeding. This single-component table is final for isolated sources.

**Phase 4:** For each confused group, run joint multi-component `imfit` (N simultaneous 2D Gaussians, seeded from Phase 0 catalog positions) per epoch. Inspect residual maps for leftover structure and refit as needed. Record deblended peak/integrated flux with propagated uncertainties.

**Phase 5 — key deliverable:** Build a per-source, per-epoch comparison of single-component vs. deblended flux (peak and integrated), expressed as fractional difference and in units of quoted uncertainty. **Produce a table and a scatter plot of bias fraction vs. angular separation/beam FWHM**, characterizing whether blending inflates integrated flux and/or suppresses peak intensity.

**Phase 6:** Recompute 1994→2015 significance (Δ = (F₂₀₁₅−F₁₉₉₄)/√(σ₂₀₁₅²+σ₁₉₉₄²), threshold |Δ|≥3) twice — once with single-component fluxes, once with deblended fluxes. **Produce a dual classification table** flagging any source (including G2) whose variability status flips once blending is corrected.

**Phase 7 — write-up:** Assemble (1) the confusion criterion and subfield list, (2) the validated single-component table, (3) the deblended table with residual diagnostics, (4) the bias table/figure, and (5) the dual variability classification table, presented as a self-contained methods correction using only the two existing archival epochs.

## Background Reading

- De Pree, C. G.; Galvan-Madrid, R.; Goss, W. M.; Klessen, R. S.; Mac Low, M.-M.; Peters, T.; Wilner, D.; Bates, J.; Melo, T.; Presler-Marshall, B.; Webb-Forgus, R. (2018), "Flux Density Variations at 3.6 cm in the Massive Star-Forming Region W49A," *ApJ Letters*, arXiv:1807.10669
