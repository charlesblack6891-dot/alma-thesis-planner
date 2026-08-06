## 0. Framing and conventions to adopt before you touch the data

You are making one measurement, repeated across a bounded set of positions and velocities: the **line-to-continuum ratio** R(v) = I_line(v)/I_cont,local of ¹²CO J=4–3 across the two nuclei of Arp 220, together with a full characterization of the 650 μm continuum against which that ratio is defined. Everything below serves that measurement.

Fix three conventions now and hold them for the whole thesis, because they will keep you from writing claims the data cannot support:

1. **Never write τ.** Write *apparent absorption depth* D(v) ≡ −ln R(v), or *line-to-continuum ratio*, and say in the text at first use that D is not an optical depth. In these nuclei the 650 μm dust and the CO are co-spatial and the dust is optically thick, so a "continuum" measurement is a nearly opaque surface at unknown depth, and CO emission from the same gas parcel fills in absorption along the identical sightline. Every D you quote is a lower bound.
2. **The sign of (I_line − I_cont) is a result, not an input.** The "deep CO absorption" in the proposal abstract refers to CO 6–5 and 3–2 in other member OUS that are not in your dataset. Whether CO(4–3) goes below the continuum here is something you will determine.
3. **Interpret in brightness temperature, not geometry.** A line appears in absorption when the continuum brightness temperature T_B,cont exceeds the CO(4–3) excitation temperature T_ex along the same gas, and in emission when it does not. Do not use the foreground-screen language ("redshifted absorption ⇒ gas falling in"); the geometry does not license it.

Set up a git repository on day one containing your CASA scripts, Python analysis notebooks, and a running lab notebook in Markdown. Every number that ends up in the thesis should be traceable to a script in that repository. Record the CASA version string in every log.

## 1. Weeks 1–2 — Retrieval, spectral-setup verification, and the QA2-first decision

**Retrieval.** Download member OUS `uid://A001/X1289/X1e6` of project 2017.1.00735.S from the ALMA Science Archive (https://almascience.nrao.edu/aq/), searching either by project code or by the OUS UID. Take the full delivery: the pipeline-calibrated measurement sets, the QA2 image products (cube and continuum), the weblog, and the calibration/imaging scripts. Untar into a read-only `raw/` tree and never edit anything inside it; all work happens in a separate `work/` tree.

**Read the weblog before the data.** The QA2 weblog tells you the achieved beam, the achieved RMS, which spectral windows were flagged, what the flux calibrator was and what model was used, and whether the pipeline did any continuum subtraction. Extract and tabulate: achieved synthesized beam (major, minor, PA) for each product, achieved continuum RMS, achieved per-channel line RMS, total on-source time, and the number of antennas and baseline range. The archive tabulates 0.086″ angular resolution, 0.746 km/s native velocity resolution, 302 s integration, line sensitivity 8.336 mJy/beam at 10 km/s, and continuum sensitivity 0.2723 mJy/beam — treat all of these as *predicted/tabulated* values and replace each with the value you measure from the delivered images. Your error budget uses your measured numbers, not the archive's.

**Verify the spectral setup from the MS header, not from the annotation.** Run `listobs` on each measurement set and, in the CASA Python environment, use `msmd` to pull the exact spectral-window edges, channel widths, number of channels, and the frame in which frequencies are recorded (TOPO vs LSRK — this matters). Confirm the four windows: 451.9–453.8, 453.6–455.6, 463.8–465.8, 465.6–467.6 GHz.

Then do the line identification yourself. The archive's line list is annotated as generated from general knowledge and flagged for verification against Splatalogue, so verify it. Query Splatalogue for ¹²CO J=4–3 and confirm the rest frequency 461.041 GHz. Apply the systemic redshift that the annotation *assumes*, z = 0.018126 (cz = 5434 km/s), and confirm for yourself that it lands at ≈452.8 GHz — this places the line in the 451.9–453.8 and 453.6–455.6 GHz pair, whose combined ~3.7 GHz spans roughly 2450 km/s. Carry the assumption explicitly: in the thesis, write "≈452.8 GHz, assuming z = 0.018126," the first several times, and state that the sky-frequency placement was confirmed against the MS header. Cross-check by converting the spw edges to LSRK velocity relative to CO(4–3) at that redshift and writing down the actual velocity range covered, in km/s relative to cz = 5434 km/s. That velocity axis is the one you will use everywhere.

Do the same Splatalogue sweep over the 463.8–465.8 and 465.6–467.6 GHz windows. The annotation offers high-J HC₃N (J=51–50, rest ≈464.0 GHz; J=52–51, rest ≈473.1 GHz) as *tentative* candidates and is itself agnostic as to whether such features would be redshifted or near-rest-frequency serendipitous. That identification is **not established**, and you are not going to establish it. Treat both of those windows as **additional continuum**. If a feature appears there, report it as a tentative, clearly flagged secondary result with the candidate identification stated as a candidate and the frame ambiguity stated alongside it — one figure and one paragraph, not a chapter.

**Commit to the QA2-first path.** Your primary analysis path is the delivered QA2 image products. Restoring a Cycle-5 Band 8 pipeline calibration requires a matched CASA version and can silently consume weeks. Therefore:

- All headline measurements — continuum photometry, Gaussian fits, the σ_D map, the sign map, the branch products — are computed from QA2 products first.
- Re-imaging with `tclean` from the calibrated MS is an **enhancement**, attempted only after the QA2-based measurements exist end-to-end.
- Write the abandonment date into your notebook now. If re-imaging has not produced a usable image by the end of week 8, you stop, and the attempt is documented as a result (what you tried, what failed, with the logs) rather than pursued.

Load the QA2 continuum image and cube into CARTA for a first visual look. Confirm you can see two compact nuclei, and record their approximate positions relative to the pointing centre RA, Dec = 233.73843, +23.50322.

## 2. Week 2–3 — Continuum imaging and nuclear photometry

Work on the QA2 continuum product. If the delivery includes per-spw continuum images, use them; also form a combined continuum from the two line-free windows (463.8–465.8, 465.6–467.6 GHz) for maximum continuum SNR, keeping the effective frequency recorded.

**Photometry and morphology.** Using CASA:

- `imstat` on several signal-free regions to measure the image RMS and confirm it against the weblog value; use the RMS you measure.
- `imfit` with a two-component 2D Gaussian model (one per nucleus) plus a zero-level term, fitted over a box enclosing both nuclei. Record for each nucleus: fitted position with uncertainty, peak intensity (mJy/beam), integrated flux density (mJy), and **deconvolved** major axis, minor axis, and position angle with uncertainties. Note explicitly whether each component is deconvolvable at all — if `imfit` returns a size consistent with the beam, report an upper limit on the size rather than a size.
- Repeat the fit with the fitting box, initial estimates, and background treatment varied, and adopt the spread across those variants as your fitting systematic. Add it in quadrature to the statistical error from `imfit`.
- Convert peak intensities to per-beam brightness temperature using the Rayleigh–Jeans relation with your measured beam and the effective frequency, and tabulate T_B,cont for each nucleus. This number is central to the interpretation in §7.

**Flux-scale error budget.** Carry the Band 8 absolute flux-scale uncertainty of roughly 10–20% as a separate, explicitly labelled column in every continuum table. State clearly in the text which quantities it touches — nuclear flux densities, any dust mass you derive, and every brightness-temperature statement — and which it does **not**: R and D are ratios formed within the same spectral setup, so the absolute scale divides out of them. Say this once, plainly, and then keep the two error columns separate throughout.

**No spectral index.** Do not attempt to measure a dust spectral index between the window pairs. Δν/ν ≈ 2.6% across the pairs, so the predicted dust-slope difference is comparable to Band 8 spw-to-spw amplitude systematics and the measurement is uninformative by construction. State this reasoning in one sentence in the methods chapter and spend those days on §3 instead.

**Bounded self-calibration.** With only 302 s on source, self-calibration may or may not be viable, so bound it: run a short ladder of phase-only solution intervals (`inf`, then a couple of shorter ones) with `gaincal`, inspect solution SNR and the fraction of failed solutions in `plotms`, and adopt self-cal only if a clear majority of solutions have acceptable SNR and the resulting image RMS improves without altering the fitted nuclear positions or sizes beyond their uncertainties. If no interval qualifies, drop self-cal, keep the diagnostic plots, and document the outcome. Do not iterate past the ladder you defined.

## 3. Week 3 — The go/no-go tier decision

This is the single most important week of the project, and it ends with a written decision.

**Measure the quantity that actually decides the project: the per-beam continuum brightness.** At 0.086″ much of Arp 220's flux may be resolved out, so the *total* flux is not what matters — the per-beam continuum intensity at each position is what sets your ability to measure R there. Produce a per-beam continuum brightness map (this is simply your calibrated continuum image in mJy/beam, but treat it as the key data product it is).

**Propagate to σ_D.** Measure the noise per velocity bin directly from line-free channels of the QA2 cube after binning to 20 km/s (the archive's tabulated 8.336 mJy/beam at 10 km/s implies roughly 5.9 mJy/beam at 20 km/s if noise scales as √Δv; verify this empirically rather than assuming it). Then, per pixel/beam,

σ_R ≈ σ_line / I_cont,  and near R ≈ 1, σ_D = σ_R / R ≈ σ_R.

Make a **σ_D map** by dividing the binned-cube RMS by the per-beam continuum map.

**The threshold, and why it is that number.** The science requires you to (i) distinguish a shallow line-to-continuum feature, |R − 1| ≈ 0.25 (D ≈ 0.3), from zero at ≥3σ, and (ii) tell a factor-of-two variation in depth across a nucleus from a flat one. Both demand σ_D ≈ 0.1. So count the beams — independent beams, not pixels; divide the qualifying area by the beam area — with σ_D < 0.1, per nucleus.

**Declare the tier in writing, in week 3, and stick to it:**

- **Tier A** — ≳20 qualifying independent beams per nucleus: build resolved maps of R, of the sign of (I_line − I_cont), of the velocity centroid, and of the line width.
- **Tier B** — a handful of qualifying beams: extract spectra at a **named, tabulated set of positions** chosen before you look at the line data: each continuum peak, plus offsets of roughly one and two beams along the major and minor axes of each nucleus's fitted continuum ellipse. Tabulate the positions with coordinates in the thesis.
- **Tier C** — few or no qualifying beams: one spatially integrated spectrum per nucleus, summed over the continuum-bright region (define that region by a continuum brightness contour and state the contour level), with all beam-scale structure reported as upper limits.

Tier C is a legitimate, complete thesis outcome. It is written into the plan now precisely so that marginal data are never over-resolved into structure that is not there. Put the tier decision, the counts that produced it, and the σ_D map into your notebook with a date, and email me the one-page summary.

## 4. Weeks 4–6 — The local continuum baseline and the systematic that dominates it

**Local, always.** The continuum reference for R must come from line-free channels *inside* the 451.9–453.8 / 453.6–455.6 GHz pair — the same windows the line sits in. Never extrapolate the continuum across the ~11 GHz gap from the 463.8–467.6 GHz pair; that introduces exactly the dust-slope uncertainty you decided in §2 you cannot measure. (The upper pair still serves as an independent, higher-SNR continuum image for the photometry of §2 and as a sanity check on morphology; it is not the baseline for R.)

**Selecting line-free channels.** In a line-rich spectrum this selection is the dominant systematic, so treat it as a measurement:

1. Form a high-SNR reference spectrum by averaging over the continuum-bright region of each nucleus.
2. Identify candidate line-free channels by iterative sigma-clipping about a low-order (order 0 or 1) fit, and separately by eye from the reference spectrum, excluding a generous velocity window around the CO(4–3) sky frequency.
3. Construct **at least two independent line-free channel selections** — for example, a conservative one that excludes a wide velocity range around the line, and a permissive sigma-clipped one — and carry both through the entire analysis.
4. Take the difference in every derived quantity (I_cont,local, R, D, centroid, width) between the two selections and **propagate it as a systematic error term**, reported separately from the statistical error in every table. If the two selections disagree by more than the statistical error on a given quantity, say so and let the systematic dominate the quoted uncertainty.

Fit the local continuum per spatial pixel with a constant (order 0) as the default; use order 1 only if the residuals in the line-free channels show a significant slope, and if you do, report both.

**The sign measurement.** With I_cont,local in hand per position, compute the sign of (I_line − I_cont,local) at every qualifying position, per velocity bin, and produce the **sign map**. This is a headline figure in its own right: it locates where the dust brightness temperature exceeds the CO excitation temperature and where it does not. Mask it at the σ_D threshold from §3 so that only significant sign determinations are coloured; render insignificant regions in a neutral colour and say so in the caption. The sign map precedes and determines which products of §6 you build.

## 5. Weeks 6–9 — Imaging the cube: narrow and binned from the start

**Do not subtract the continuum.** Continuum subtraction — whether `uvcontsub` in the visibility domain or a spectral baseline in the image domain — destroys the sign information on which the entire thesis rests. Image the line *with* the continuum in place. Say this explicitly in the methods chapter so no reader assumes the standard recipe was followed.

**Image narrow and binned.** The native 0.746 km/s channels are unusable per beam at 8.336 mJy/beam per 10 km/s and 302 s on source, so never produce a full-resolution four-spw cube. Instead:

- Restrict the imaged frequency range to the CO(4–3) velocity range you derived in §1 — enough to cover the systemic line plus wings on both sides, with a comfortable margin of line-free channels at each end for the baseline of §4.
- Bin to **10–20 km/s at the imaging stage** (`width` in `tclean`, in channels or velocity), not afterwards. Pick 20 km/s as the working default and produce a 10 km/s version only if the σ_D map at 20 km/s is comfortably below threshold over many beams.
- Image in LSRK with `restfreq` set to the ¹²CO J=4–3 rest frequency 461.041 GHz so the cube carries a velocity axis directly.
- Use Briggs weighting; run at least two robust values (e.g. 0.5 and 2.0) and compare. If sensitivity is marginal, the more naturally weighted cube may be the one your tier decision is based on — in that case re-run the §3 σ_D counting on it and record the beam actually achieved.
- Clean conservatively: shallow thresholds set at a few times your measured RMS, with a clean mask restricted to the continuum-bright region. Because you are imaging absorption *and* emission in the same cube, ensure your masking and any auto-masking parameters do not suppress negative features — check this explicitly on a test channel and note the check in your log.

The 463.8–465.8 and 465.6–467.6 GHz windows are imaged as continuum only (`specmode='mfs'`), as in §2.

**Consistency check.** Before proceeding, verify that a spectrally averaged version of the line cube over line-free channels reproduces the continuum photometry of §2 within the errors. If it does not, resolve the discrepancy before going further.

## 6. Weeks 9–11 — Branch products at the selected tier

Build only the products dictated by your sign map and your tier. The most likely and most interesting outcome is **mixed**: some positions or velocity bins in absorption, others in emission. In that case compute each branch's products on its own subset, over a common set of positions so the two are directly comparable.

**Absorption branch** — where R < 1 significantly:

- D(v) = −ln R(v) per velocity bin, with statistical and line-free-selection systematic errors.
- Peak D and the velocity at which it occurs.
- The **absorption-weighted velocity centroid**, ⟨v⟩ = ∫ D(v) v dv / ∫ D(v) dv, quoted relative to cz = 5434 km/s (state that this systemic velocity is the assumed z = 0.018126 value).
- The absorption FWHM, measured both directly from the profile and from a single-Gaussian fit to D(v); if the profile is clearly non-Gaussian, report the direct measurement and show the fit residuals.
- ∫ D(v) dv, the integrated apparent depth, for §6's column-density table.

**Emission branch** — where R > 1 significantly:

- Integrated line flux over the same positions.
- Moment maps computed on the **continuum-subtracted-in-post** line component (I_line − I_cont,local, formed after the fact from your local baseline, never from a `uvcontsub`ed cube): moment 0 (integrated intensity), moment 1 (velocity field), moment 2 (velocity dispersion), each masked at your significance threshold and each with the mask criterion stated in the caption.
- The continuum-referenced line-to-continuum contrast, R − 1, at the same positions, so the emission and absorption branches are reported on a common axis.

**Position–velocity diagrams.** Where the tier supports it (Tier A, and Tier B if the tabulated positions are numerous enough along an axis), extract PV cuts with `impv` along the major axis of each nucleus as defined by the deconvolved continuum Gaussian fit from §2, and a matching minor-axis cut. Extract them from the **non-continuum-subtracted** cube so absorption and emission appear in their true sense, and mark the continuum level on the colour scale. Use the same slit width and the same velocity range for both nuclei so the two panels can be compared directly.

**Comparing the two nuclei.** Whatever the branch, produce one figure and one table that put east and west side by side on identical axes and identical colour stretches: continuum peak and T_B,cont, R and its sign, centroid, and width.

**Column densities — a short table, not a chapter.** Compute CO column densities on a **grid of assumed excitation temperatures** (e.g. T_ex = 30, 50, 100, 200 K spanning the plausible range for mid-J CO in these nuclei), using the standard LTE relation with the CO(4–3) Einstein A coefficient and partition function from your Splatalogue/CDMS query. For the absorption branch, integrate ∫ D(v) dv treating D as though it were an optical depth *for the purposes of the formula only*, and label every resulting number a **lower limit**; for the emission branch, use the optically thin LTE emission formula and likewise label the results lower limits. One table, one paragraph explaining the assumed-T_ex grid and why the entries are lower limits, and move on. Do not run or write a radiative-transfer code; it is out of scope for this thesis and the data do not constrain the additional free parameters.

## 7. Weeks 11–13 — Interpretation and write-up

Lead the interpretation with **T_B,cont versus T_ex**. You have measured T_B,cont per beam in §2. Where the line is in absorption, T_B,cont exceeds the CO(4–3) excitation temperature along that gas; where it is in emission, it does not. Use the sign map to state, position by position, on which side of that inequality each part of each nucleus falls, and use the T_ex grid from §6 to bracket what that implies.

Then describe the **velocity structure of R**: how the centroid and width vary across each nucleus, and whether the variation is ordered (e.g. monotonic along a major axis, as a rotating disk with an internal excitation or temperature gradient would produce) or unordered. Compare the two nuclei explicitly — differences in continuum brightness, in the sign of R, and in centroid offset relative to cz = 5434 km/s are the substance of your result.

Only at the end, and briefly, revisit the infall-versus-outflow motivation that the program was proposed to address. State plainly that because the dust is optically thick and co-spatial with the CO rather than a background screen behind a foreground absorber, the directional inference "redshifted absorption implies foreground gas falling in" is not licensed here — not even as a preferred reading — and name the models your data cannot distinguish. Keep this bounded: a section, not a chapter.

**Nomenclature audit before submission.** Grep your own draft for "optical depth," "τ," "outflow," and "infall," and confirm every instance is either a quotation of the program's motivation or explicitly flagged as unlicensed by these data.

## 8. Tools

CASA for retrieval-adjacent inspection and all imaging and image analysis: `listobs`, `msmd`, `plotms`, `tclean`, `gaincal`/`applycal` (bounded self-cal only), `imstat`, `imfit`, `immoments`, `impv`, `specflux`, `imsubimage`, `imhead`. CARTA for interactive cube inspection. Python for everything downstream: `astropy` (FITS I/O, WCS, units, coordinates), `spectral-cube` and `radio-beam` for cube handling and beam bookkeeping, `numpy`/`scipy` for baseline fitting, sigma-clipping, Gaussian fits and error propagation, and `matplotlib` (with `astropy.visualization` / WCSAxes) for all figures. Splatalogue for line identification and molecular constants. No radiative-transfer code, no ancillary datasets, no additional observations.

## 9. Deliverables

1. A 650 μm continuum image of the Arp 220 nuclear region with nuclear photometry, deconvolved sizes (or size upper limits), per-beam brightness temperatures, and an explicit two-column error budget separating measurement error from the ~10–20% Band 8 flux-scale uncertainty.
2. A documented record of the QA2-versus-re-imaging outcome and the bounded self-calibration outcome, including diagnostic plots for whichever path was abandoned.
3. The per-beam σ_D map and the dated, written week-3 tier decision with the qualifying-beam counts that produced it.
4. The CO(4–3) sign map of (I_line − I_cont,local), significance-masked.
5. Branch-appropriate line products at the selected tier: D(v), peak depth, absorption-weighted centroid and FWHM for absorption regions; integrated flux and moment 0/1/2 maps for emission regions; R − 1 for both.
6. PV diagrams along each nucleus's continuum major and minor axes where the tier supports them.
7. A short lower-limit CO column-density table on the assumed-T_ex grid.
8. One clearly flagged tentative-secondary figure and paragraph if any feature appears in the 463.8–467.6 GHz windows, with the HC₃N candidate identification stated as unestablished.
9. The analysis repository, with every thesis number traceable to a script.
