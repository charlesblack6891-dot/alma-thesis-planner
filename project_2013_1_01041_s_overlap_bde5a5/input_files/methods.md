## 0. Conventions fixed at the start

Adopt a single distance and kinematic reference and use them everywhere: D = 22 Mpc (1″ ≈ 107 pc, so the native 0.268″ beam ≈ 29 pc and the headline 0.5″ beam ≈ 54 pc), and v_sys = 1610 km/s in the radio LSRK convention (z = 0.00537). Every velocity in the thesis is LSRK radio; every offset velocity is relative to a clump's own centroid, never to v_sys. Useful conversion to memorize: at 219 GHz, T_b/I = 1.222×10⁶/(ν_GHz² θ_maj θ_min) K per Jy/beam, i.e. ≈ 102 K (Jy/beam)⁻¹ for a 0.5″ circular beam and ≈ 355 K (Jy/beam)⁻¹ at the native 0.268″ beam. That factor is why we taper: the same flux limit buys roughly 2× better brightness sensitivity at 0.5″ once the per-beam noise penalty of down-weighting long baselines is paid.

Software: CASA 6.x for retrieval, continuum subtraction, and imaging; Python (astropy, spectral-cube, radio-beam, astrodendro, numpy/scipy, matplotlib, emcee only if needed for the stretch goal) for everything downstream. All analysis lives in one git repository, driven by scripts that read a single YAML configuration file. No parameter is ever typed into a notebook by hand.

## 1. Week 1 — scope confirmation and line verification

Query the ALMA archive entry for 2013.1.01041.S and its bibliographic links, and run one ADS search on the project code and on "Antennae SiO HNCO overlap" to confirm no published clump-level SiO/HNCO census exists from this OUS. Record the search strings and date in the repository; the census and the velocity-resolved stack are the deliverable either way, so this step bounds framing, not the work.

In the same week, verify every line identification in Splatalogue at the observed frequency, not the rest frequency. Compute ν_obs = ν_rest/1.00537 and confirm each falls in a spectral window with at least ±150 km/s of clean baseline on both sides: SiO(5–4) 217.10498 → 216.006 GHz; HNCO(10₀,₁₀–9₀,₉) 219.79827 → 218.624; C¹⁸O(2–1) 219.56036 → 218.387; ¹³CO(2–1) 220.39868 → 219.221; H₂CO(3₀,₃–2₀,₂) 218.22219 → 217.056; CH₃OH(4₂,₂–3₁,₂ A⁺) 218.44006 → 217.274. Then do the contaminant sweep: list every catalogued transition within ±200 km/s of each target line and flag it in the config. Two you will certainly find — HC₃N(24–23) at 218.3247 GHz rest sits only ~140 km/s from H₂CO(3₀,₃–2₀,₂), and c-C₃H₂ at 217.822/217.940 GHz rest lands in the same window — so the H₂CO integration window in §6c must be narrow enough to exclude HC₃N, and you will state that width in the config before measuring anything. ¹³CO(2–1) sits near the upper edge of the 217.8–219.7 GHz window; check in the actual header where the band edge falls and how much line-free baseline survives on the high-frequency side. If ¹³CO is edge-truncated, that is the moment to discover it, not in month 3.

## 2. Months 1–2 — cubes, with a hard handoff date

**Retrieval.** Download the QA2 products and the pipeline-calibrated measurement set for `uid://A001/X12a/X4e` via astroquery.alma. Inspect the QA2 cubes first: check the delivered channel width, the spectral coverage per window, the restoring beams, and whether the delivered cubes are continuum-subtracted. If the QA2 cubes cover the six lines at usable channel width with sane beams, use them and skip re-imaging; the schedule assumes you will re-image only for the two faint shock lines if the delivered products are unusable.

**Continuum subtraction.** Identify line-free channels per spectral window from a spatially-averaged spectrum over the bright emission, excluding ±200 km/s around every line in your Splatalogue table. Run `uvcontsub` with `fitorder=1` and the line-free channel selection recorded in the config. Keep the continuum-only visibilities.

**Line cubes.** Image each line with `tclean`, `specmode='cube'`, `outframe='LSRK'`, `gridder='mosaic'` (the observation is a mosaic — do not use `standard`), `deconvolver='multiscale'` with scales [0, 5, 15, 45] pixels, `weighting='briggs'` with `robust=0.5`, `usemask='auto-multithresh'`, `pbcor=True` on the final products, and `restoringbeam='common'`. Cell 0.05″; velocity coverage 1300–1900 km/s per line. Produce the headline set with `uvtaper` tuned to give a 0.5″ circular restoring beam — iterate the taper on a single line first, then apply the same taper to all six. Channel binning: keep ¹³CO, C¹⁸O, and H₂CO/CH₃OH at 2–3 km/s; bin SiO and HNCO to 10 km/s to match the quoted sensitivity. Also produce a native-resolution (robust=0.5, no taper) set for the appendix only.

**Continuum image.** Make one 1.3 mm mfs image from the 231.4–233.4 and 233.2–235.2 GHz windows using the line-free channels (after excluding the CH₃OH/SO₂ candidates you flagged), `nterms=1`, `gridder='mosaic'`, robust=0.5, tapered to the same 0.5″ beam.

**Common grid.** Before anything is measured, regrid every cube — headline and appendix sets separately — onto an identical spatial pixel grid and convolve to an identical circular beam using `imsmooth`/`radio-beam`. Verify with an assertion in code that all headers agree on CRVAL, CDELT, and BMAJ/BMIN/BPA. Aperture photometry across cubes is meaningless otherwise.

**Noise characterization.** For each cube, build a per-pixel, per-channel noise map: take the flat-noise (non-pbcor) cube, compute the rms in line-free channels per pixel with a median-absolute-deviation estimator, then divide by the primary-beam response map to get the noise map on the pbcor grid. Sanity-check that the flat-noise rms is spatially near-uniform and that the resulting SiO noise at the mosaic center is within a factor of ~2 of the 0.975 mJy/beam per 10 km/s scaled by the tapering penalty you measured. Everything downstream — the depth mask, the upper limits, the stacking weights — is read off these maps, never off a predicted sensitivity.

**Handoff.** Set a calendar date at the end of month 2. Month 3 begins on whatever cubes exist that day. If a line is not imaged by then, it is dropped from the headline analysis and that is recorded.

## 3. Month 3 — one clump catalog

Segment the **0.5″ ¹³CO(2–1) cube only**. Run astrodendro on the flat-noise cube with `min_value = 3σ`, `min_delta = 2σ`, and `min_npix` equal to two spectral channels times one beam area in pixels, where σ is the median line-free rms. Keep **leaves only** — no trunk or branch structures enter the catalog. Expect a few tens of objects; if you get hundreds, your min_delta is too permissive and you are cataloguing noise ridges, so check by rerunning on the inverted (negated) cube and confirming near-zero spurious leaves at your thresholds.

For each leaf, measure CPROPS-style moments on the pbcor cube within the leaf mask: intensity-weighted centroid position and velocity; second moments σ_maj, σ_min, σ_v; peak and integrated ¹³CO intensity. Apply the two standard corrections and report both raw and corrected values: extrapolate the moments to the 0 K isosurface (linear extrapolation in the moment-vs-threshold curve), and deconvolve the spatial sizes as σ_dec = √(σ_obs² − σ_beam²), flagging as unresolved anything where σ_obs < 1.1 σ_beam. Convert to a deconvolved radius R = 1.91 σ_dec (in pc) and FWHM linewidth ΔV = 2.355 σ_v.

Add the **uv-filtering diagnostic** for each clump: on the ¹³CO moment-0 map, measure the mean surface brightness in an annulus from 1.5R to 3R and divide it by the clump's peak. Any clump whose annulus mean is more negative than −10% of its peak is flagged `bowl_flag=True`. These clumps stay in the catalog and in the census; the flag is carried through every table and every figure so the reader can see whether the result depends on them.

Use C¹⁸O(2–1) as a check, not an input: extract C¹⁸O over each ¹³CO leaf footprint, record the C¹⁸O velocity centroid where detected at ≥3σ, and record the ratio I(¹³CO)/I(C¹⁸O). Where that ratio falls well below the assumed abundance ratio (adopt [¹³CO]/[C¹⁸O] = 8), flag the clump as optically thick in ¹³CO — the column derived in §4 is then a lower limit and the clump is annotated as such.

## 4. Month 4 — a denominator defined by physics

Two cuts, both fixed in the config before any SiO cube is opened.

**Column cut.** Convert the ¹³CO peak brightness temperature and linewidth into a peak H₂ column under LTE with a fixed T_ex = 20 K, optically thin ¹³CO, and CMB background subtraction:

N(¹³CO) = (8πν³/c³) · [Q(T_ex)/(g_u A_ul)] · exp(E_u/kT_ex) · [exp(hν/kT_ex) − 1]⁻¹ · ∫T_R dv,

with E_u = 15.87 K, A_ul = 6.04×10⁻⁷ s⁻¹, g_u = 5, and Q(T) ≈ 2kT/hB + 1/3 for B = 55.101 GHz. Then N(H₂) = N(¹³CO)/X(¹³CO) with X(¹³CO) = 2×10⁻⁶ (from CO/H₂ = 10⁻⁴ and ¹²C/¹³C = 50). Set the cut at a round number safely above your completeness limit — compute the N(H₂) corresponding to a 5σ ¹³CO peak at the median linewidth, round up to the next factor-of-two-clean value (this will land near 10²² cm⁻²), and freeze it. Quote every assumption in the same table as the cut.

**Depth cut.** From the SiO noise map, compute the 3σ integrated-intensity limit per pixel over a fixed 40 km/s window, and define the census footprint as the contiguous region where that limit is below a stated uniform value (choose the value so the footprint covers most of the mosaic's high-response area; read it off the map, do not guess). Only clumps whose ¹³CO peak position lies inside this footprint enter the census.

Every clump excluded by either cut goes into a separate table with the reason for exclusion. The census fraction is quoted only over the surviving sample.

**Pre-registration mechanics.** At the end of month 4, commit and tag the config file containing: the column cut, the depth threshold, the integration-window rule, the detection criterion, the stacking weights, the H₂CO ratio threshold, and the inconclusiveness test of §6c. Until that tag exists, you do not extract a single SiO or HNCO spectrum. This is the whole reason the result is quotable.

## 5. Months 5–6 — measurement

For every surviving clump, extract SiO and HNCO spectra by averaging over the clump's ¹³CO leaf mask projected onto the sky (the 2D union of the mask across velocity), on the common-grid, common-beam pbcor cubes. Integrate over a fixed window centered on the clump's C¹⁸O centroid where available, else its ¹³CO centroid, with half-width max(1.5 × FWHM(¹³CO), 20 km/s), capped at ±40 km/s.

Compute the uncertainty on the integrated intensity as σ_I = σ_chan · Δv_chan · √(N_chan) / √(N_beam), where σ_chan is the aperture-averaged noise from the noise map, N_chan is the number of channels in the window, and N_beam is the number of independent beams in the aperture. Verify this empirically rather than trusting it: place several hundred apertures of the same size at random positions inside the depth footprint but off the clumps, integrate over the same window width, and confirm the measured scatter matches σ_I within ~20%. If it does not, use the empirical scatter.

**Detection criterion (single, pre-registered):** I ≥ 3σ_I in the fixed window. As a confirmation check reported alongside — never as an alternative criterion — require that the detection show ≥2 contiguous channels above 2.5σ in the 10 km/s-binned spectrum. Non-detections get a 3σ upper limit, I_lim = 3σ_I, with the local noise value attached to the catalog row.

## 6. Months 7–9 — three results

**(a) Column-selected detected fraction.** Report N_det/N_sample for SiO, for HNCO, and for either-line, each with a Wilson score 95% interval. Every quotation of the fraction appears in the same sentence as the column cut and the limiting depth — write it that way in the abstract, the results, and every figure caption. Report the fraction once more with `bowl_flag` clumps removed, in the same table.

**(b) Velocity-resolved stack.** Shift each clump's SiO and HNCO spectrum onto a velocity-offset axis defined by its C¹⁸O centroid (¹³CO where C¹⁸O is undetected; record which was used per clump), resample onto a common 10 km/s grid spanning ±100 km/s so the ±30 km/s offsets the science motivates are well inside the window, and co-add with inverse-variance weights (weights fixed in the config). Produce three stacks: all clumps, non-detections only, and detections only. The headline figure is stacked SiO and HNCO intensity versus velocity offset, with the ¹³CO stack overplotted as the bulk-gas reference, plus a companion panel showing stacked S/N as a function of integration-window width from 10 to 100 km/s.

Run three null tests and show at least the first: stack at the same positions but with each clump's velocity offset randomized; stack at random off-clump positions inside the depth footprint; and jackknife the sample by leaving out one clump at a time, reporting the spread. Uncertainties on stacked quantities come from bootstrap resampling of the clump list (10⁴ draws), not from the propagated σ_I alone.

Report line strengths as **intensity ratios** I(SiO)/I(¹³CO) and I(HNCO)/I(¹³CO) computed from the stacks. Do not convert to abundances anywhere — one transition per species constrains no excitation. Secondary split: divide the sample into ¹³CO linewidth quartiles and show the four binned stacks in one panel. No per-clump ratio distributions, no correlation coefficients on limits.

**(c) Column-matched selectivity test.** Measure I(H₂CO 3₀,₃–2₀,₂) for every clump using a window narrow enough to exclude HC₃N(24–23) at +140 km/s (state the width; ±60 km/s is the natural choice). Form R_H₂CO = I(H₂CO)/I(¹³CO) and split the sample at the threshold you froze in month 4 (the sample median of R_H₂CO computed on ¹³CO and H₂CO alone, before any SiO spectrum is opened).

Match the two halves in column: bin all clumps in I(¹³CO) using bins of fixed width in log I, and within each bin keep equal numbers of H₂CO-bright and H₂CO-faint clumps (random subsampling, averaged over 10³ realizations). Stack SiO within each matched sample and compare I(SiO)/I(¹³CO) between them, with bootstrap confidence intervals on the difference.

Before interpreting anything, run the pre-registered overlap test: a two-sample KS test on the I(¹³CO) distributions of the H₂CO-bright and H₂CO-faint halves. If p < 0.05, or if fewer than three I(¹³CO) bins contain at least two clumps of each type, the test is reported as **inconclusive** and the stacks are shown without a claim. Write that sentence into the config file now so you cannot be tempted later.

## 7. Continuum

Use the 1.3 mm image for one purpose only: overlay the continuum ≥5σ contours on the clump catalog and set a boolean `cont_flag` for clumps with a coincident continuum peak, noted in the text as "possibly hosting an embedded HII region." Band 6 alone cannot separate dust from free-free, so no continuum-derived mass, no spectral index, no dust column enters the thesis.

## 8. Appendix robustness table (one page, once)

Repeat §6a — the fraction and its Wilson interval — for exactly two variants: the native-0.268″ catalog and cubes (with the depth and column cuts recomputed from that configuration's own noise map), and a C¹⁸O-based column and centroid variant at 0.5″. One table, three rows, no discussion in the main text.

## 9. Optional stretch, only if months 7–8 finish early

For the brightest few SiO detections, compute LTE column densities over an assumed T_ex grid of 20–100 K and plot N(SiO) versus T_ex so the assumption's effect is visible on the page. This is a figure with a caption, not a result.

## 10. Deliverables and reproducibility

The repository ships: the 0.5″ cubes and moment-0/1/2 maps for all six lines plus the continuum image; one machine-readable clump catalog (FITS table and CSV) with position, deconvolved size, velocity centroid, linewidth, peak and integrated ¹³CO, N(H₂), C¹⁸O centroid and ratio, H₂CO intensity, R_H₂CO, SiO and HNCO integrated intensities or 3σ limits with local noise, `bowl_flag`, `cont_flag`, and exclusion reasons; the tagged pre-registration config; the three headline figures; and the appendix table. Every figure is regenerated by one script from the catalog and the config, with no manual steps. Run that regeneration from a clean checkout before you submit.
