# Methods

## 0. Orientation and what you are actually measuring

Everything below is built around one measurable: the ratio of two integrated line intensities of the *same* molecule, SiO, measured in the *same* solid angle, over the *same* velocity interval, in seven sources. Every step in the workflow exists to make that ratio defensible. Keep that in mind when you are tempted to skip a homogenization step — a ratio computed from cubes with different beams, different spatial grids, different velocity channels, or different primary-beam responses is not a physical quantity, it is an artifact.

## 1. Line-list verification (do this before you download anything)

The line identifications you were handed came with an explicit warning in the data description that they were generated from general knowledge and must be verified against Splatalogue before imaging. Treat them as hypotheses.

1. In Splatalogue (and cross-check in CDMS and JPL), pull the full entries for SiO J=7–6 (quoted at 303.927 GHz), SiO J=8–7 (quoted at 347.331 GHz), and ¹²CO J=3–2 (quoted at 345.796 GHz). Record, for each: the rest frequency to the quoted precision, the quantum-number assignment, the vibrational state (make sure you have v=0, not a vibrationally excited SiO line), the upper-state energy E_u, the degeneracy g_u, and the Einstein A_ul. Record which catalog entry you adopted and its uncertainty.
2. Download or tabulate the CDMS partition function Q(T) for SiO on its standard temperature grid; you will interpolate it later. For a sanity check you can compare against the linear-rotor approximation Q ≈ kT/(hB) + 1/3.
3. Build a candidate-contaminant list: for each of the three target lines, query a ±100 km/s window around the rest frequency for any other catalogued transition of comparable strength (SO₂ in particular has a dense forest through Band 7, and the annotation flags it as spread across nearly all of these windows). You need to know in advance whether a blend can masquerade as a broad SiO wing.
4. The data description states that these are Galactic sources within a few hundred pc, so no redshift correction is applied and rest frequencies are used directly. Adopt that. But you still need each source's systemic v_LSR, and you will measure that from the data itself (Step 6), not assume it.

Write this up as Table 1 of the thesis. It is a small table and it is load-bearing: the entire excitation analysis is a function of A_ul, E_u, and g_u.

## 2. Archive selection and audit

Only two of the five tunings in project 2017.1.01053.S matter for this project. Verify this yourself against the observation table rather than taking my word for it:

- **Tuning "T300"** (windows 300.1–302.1, 302.0–304.0, 312.1–314.1, 314.0–316.0 GHz; listed velocity resolution 1.078 km/s) is the only tuning whose coverage contains SiO 7–6 at 303.927 GHz. Member OUS: `X1288/Xfcc` (HH 212), `Xfcf` (IRAS 04166+2706 and L1551 IRS 5), `Xfd2` (CG 30), `Xfd5` (HH 46), `Xfd8` (GAL 331.5−00.1), `Xfdb` (BHR 71).
- **Tuning "T345"** (windows 345.2–347.2, 347.1–349.1, 357.1–359.1, 359.0–361.0 GHz; listed velocity resolution 0.943 km/s) contains SiO 8–7 at 347.331 GHz *and* ¹²CO 3–2 at 345.796 GHz. Member OUS: `Xf93` (HH 212), `Xf96` (IRAS_0416+2706 and L1551 IRS 5), `Xf99` (CG 30), `Xf9c` (HH 46), `Xf9f` (GAL 331.5−00.1), `Xfa2` (BHR 71).

That is twelve member OUS, fourteen target rows. Download the pipeline-calibrated measurement sets and QA2 image products for those only, via the ALMA Science Archive query interface or `astroquery.alma`. Log SHA/file manifests as you go.

Now audit, before you merge anything:

- **Names.** The archive lists `IRAS_0416+2706` (in T345, `Xf96`) and `IRAS_04166+2706` (in T300, `Xfcf`) at identical coordinates, 64.92708, +27.22667. Confirm from the coordinates and the weblog that these are the same source and one is a typo; document the decision.
- **Pointing centres.** Do not assume the two tunings share a phase centre. HH 46 is listed at 126.44375, −51.0125 in T345 and at 126.43236, −51.00992 in T300 — an offset of roughly half an arcminute, which is comparable to the ACA 7 m primary-beam FWHM at Band 7. Compute the angular offset for every source explicitly (`astropy.coordinates.SkyCoord.separation`). Wherever an offset is non-negligible, your usable field is the *intersection* of the two primary beams, and that intersection constrains where you are allowed to put apertures (Step 5).
- **Declinations and the abstract.** Three targets (HH 212, IRAS 04166+2706, L1551 IRS 5) sit at northern declinations despite the proposal abstract's "seven southern outflows" phrasing. Note it, reconcile it against the target coordinates, and move on; it does not affect the analysis but a reader will notice.
- **Per-source spectral window edges.** This is the audit item most likely to change your source list. The tabulated windows are not identical across targets: for GAL 331.5−00.1 the T300 windows are listed as 300.1–302.1, 301.9–303.9, 312.0–314.0, 313.9–315.9 GHz, i.e. shifted ~0.1–0.2 GHz low relative to the other six, which places SiO 7–6 at 303.927 GHz at or just beyond the upper edge of the 301.9–303.9 GHz window. For HH 46 and others the line sits ~73 MHz (≈70 km/s) below the 304.0 GHz edge, which leaves little line-free bandwidth on the high-frequency side for baseline fitting. Open each measurement set, read the actual per-spw frequency edges and frame from the data (`listobs`, `msmd`, or the weblog spw table), convert the SiO 7–6 rest frequency into the observed frame using the source systemic velocity, and confirm coverage source by source. Any source where SiO 7–6 falls outside the recorded coverage cannot enter the two-transition analysis and is carried through the rest of the workflow as a CO-plus-SiO-8–7 entry with an explicit statement of why.
- **Weblog.** For each member OUS, read the QA2 weblog: flux calibrator and model used, achieved sensitivity versus the quoted line sensitivity, restoring beam, any QA flags, number of antennas, and whether Hanning smoothing was applied (this determines channel-to-channel noise correlation and therefore your error bars).

## 3. Imaging

Use the QA2 cubes as your primary products and re-image as verification.

**Primary path.** Take the pipeline `.image` cubes plus the corresponding `.pb` images for the spws containing SiO 7–6, SiO 8–7, and CO 3–2. Continuum-subtract in the image plane only if you must; preferentially do it properly in the *uv* plane on the calibrated MS with `uvcontsub`, fitting a first-order polynomial to channels you have verified are line-free from the audit in Step 1 (contaminant list) and from a first-pass inspection of the spatially integrated spectrum. Record the fit ranges.

**Verification path.** Re-image the same three spws from the calibrated MSs with `tclean`, using identical settings for both tunings: same `cell` and `imsize` in angular units, same Briggs `robust`, same `specmode='cube'` with `restfreq` set explicitly to your Step-1 verified value, `outframe='LSRK'`, `perchanweightdensity=True`, and shallow cleaning to a threshold of ~3× the per-channel rms with a hand-drawn or auto-multithresh mask. **Impose a common uv-range in kλ across both tunings.** The two tunings are ~304 and ~347 GHz; the same physical ACA baselines correspond to different spatial frequencies at the two, so without a matched uv-range in wavelengths the two cubes are sensitive to different angular scales and your ratio inherits a spatial-filtering bias. Set the range from the intersection of the two uv-coverages. Compare the verification-path integrated intensities against the QA2-path values for two or three apertures; agreement within the calibration uncertainty is your justification for using whichever set you adopt.

Apply the primary-beam correction (`impbcor`, or divide by `.pb`) *before* any photometry, and keep the uncorrected cube for noise measurement — the noise in a pbcor cube is position-dependent.

## 4. Homogenization

This is the methodological core of the thesis. Do it in this order and check the result after each stage.

1. **Common beam.** Read every restoring beam from the headers (`imhead`). The listed resolutions across the two tunings span 3.195″ to 4.582″ (the coarsest being IRAS 04166+2706 in T300, `Xfcf`). Choose a single circular target beam that is comfortably coarser than all of them — 5.0″ is the natural choice — and convolve every cube to it with `imsmooth(kernel='gauss', targetres=True, ...)` or `spectral_cube.convolve_to`. Verify the output header beam is exactly your target in every cube. Never convolve to a beam smaller than any input.
2. **Common spatial grid.** Build one template image per source (a tangent-plane grid centred on the T345 pointing centre, with a cell of ~1″ so the 5″ beam is well sampled) and `imregrid` both tunings onto it. Sinc/linear interpolation is fine at this oversampling; state which you used.
3. **Common velocity grid.** Convert both cubes to LSRK velocity with the verified rest frequencies (`imreframe` if needed, then `imregrid` on the spectral axis, or `spectral_cube.spectral_interpolate`). The two tunings are listed at 1.078 and 0.943 km/s; regrid **both** to a single coarser grid — do not upsample the coarser one. Use 2.0 km/s channels for the SiO ratio work (this buys S/N and makes the channel-correlation bookkeeping simpler) and retain a 1.5 km/s version of CO 3–2 for kinematics. Smooth spectrally before decimating (`specsmooth`) so you are not aliasing.
4. **Common brightness units.** Convert every cube from Jy/beam to K using the Rayleigh–Jeans relation T_b [K] = 1.222×10⁶ × I [Jy/beam] / (ν[GHz]² θ_maj[″] θ_min[″]). **This is not cosmetic.** Because the two SiO transitions are at different frequencies, a flux ratio and a brightness ratio differ by (ν₇₋₆/ν₈₋₇)²; doing the excitation analysis in Jy/beam is the single most common way to get this analysis wrong by tens of percent. Do all subsequent arithmetic in K.
5. **Flux-scale consistency.** From the weblogs, tabulate the flux calibrator and adopted flux density per member OUS. Where the same calibrator and model were used for both tunings, the ~10% Band 7 absolute calibration uncertainty partially cancels in the SiO ratio; where they differ, it does not. Carry the correlated and uncorrelated parts separately (Step 8).
6. **Common footprint mask.** Build a per-source mask that is `True` only where the primary-beam response exceeds 0.5 in **both** tunings, after regridding. For HH 46 this will be a markedly smaller region than for the other sources, because of the pointing offset found in Step 2. All apertures must lie inside this mask.

Save the homogenized cubes as FITS with a documented header history. These are a thesis deliverable in their own right.

## 5. Aperture definition

Three apertures per source, each a circle of diameter equal to the common beam (5″), all inside the Step-4.6 mask:

- **Aperture C (driving source):** centred on the continuum peak from the QA2 aggregate continuum image of the T345 member OUS (continuum sensitivities in this project run ~0.26–0.73 mJy/beam, adequate for centroiding a detected source, and the annotation is explicit that the continuum here supports source/driving-position identification rather than dust modelling). If no continuum source is detected above 5σ inside the mask, fall back to the peak of the low-velocity CO 3–2 moment-0 map and say so.
- **Apertures B and R (blue and red lobes):** centred on the peaks of the high-velocity blue and red CO 3–2 moment-0 maps (velocity intervals from Step 6). Require the aperture centre to be at least one beam from the aperture-C centre so the three are quasi-independent; if the lobes are unresolved at 5″ and no distinct peak exists, place B and R at the ±1-beam positions along the position angle of maximum high-velocity CO elongation and record that this source's lobes are spatially unresolved.

Record all aperture centres in a table, with the primary-beam response of each tuning at each centre. Extract spectra with `specflux` or by masked averaging over the aperture in the K-unit cubes; because the aperture is one beam across, an average (not a sum) is the right statistic and is directly comparable between lines.

## 6. Systemic velocity and velocity intervals

1. **Systemic velocity.** For each source, take the CO 3–2 spectrum in aperture C, and define v_sys as the centroid of the narrow ambient component (fit a single Gaussian to the low-velocity core, masking the wings). Cross-check against a narrow dense-gas line in the same tuning if one is well detected. Report v_sys with its fit uncertainty. Do not import v_sys from the literature; you have the data, and one of your sources may sit at a substantially non-local velocity, which the audit will reveal.
2. **Velocity intervals from CO itself.** In each aperture, define, relative to v_sys: a **low-velocity** interval |v − v_sys| < v_lo and a **high-velocity** interval v_lo < |v − v_sys| < v_max, with v_lo set where the CO 3–2 profile in that aperture transitions from the ambient core to the wing (identify it as the velocity at which the profile departs from the fitted ambient Gaussian by more than 3σ). Apply the *same* intervals to SiO 7–6 and SiO 8–7 in that aperture. This is the point of the exercise: matched velocity intervals across all three lines, defined by the data and not by a literature convention.
3. **v_max, the ranking variable.** Measure the maximum CO 3–2 velocity extent per source in a way that is uniform across sources of differing sensitivity. Convert the quoted line sensitivities (7.2–20.2 mJy/beam at 10 km/s) into brightness temperature in the common 5″ beam with the formula in Step 4.4, take the *worst* value across the sample as a uniform brightness threshold T_thr, and define v_max as the largest |v − v_sys| at which the CO 3–2 profile, binned to a fixed 2 km/s, exceeds T_thr in two consecutive channels. Report v_max,blue, v_max,red, and max(|v|) per source. Using a fixed brightness threshold rather than a per-source nσ threshold is what makes the ranking meaningful; state this explicitly.

## 7. Line measurement, detections, and limits

For each aperture and each of the three lines, in each velocity interval:

- Measure the per-channel rms σ_chan in emission-free channels of the same aperture in the same cube, on the *non*-pbcor cube, then scale to the aperture's primary-beam response.
- Integrate: W = Σ T_b Δv over the interval. Propagate σ_W = σ_chan Δv √(N_chan) × √f, where f is the channel-correlation factor (f > 1 if Hanning smoothing was applied in the pipeline or by you in Step 4.3; determine it empirically from the autocorrelation of the noise spectrum rather than assuming a value).
- Declare a detection at W > 5σ_W with a visually confirmed, kinematically sensible profile; declare a marginal detection at 3–5σ_W; otherwise report a **3σ upper limit** W < 3σ_W over the same interval. Non-detections are results. They go in the table with their limits, and they propagate into the excitation analysis as one-sided constraints on T_ex and N(SiO) — they are not dropped, and they are not replaced by zero.
- Independently fit each detected SiO profile with a Gaussian (or two, if the profile demands it) using `pyspeckit` or `scipy.optimize.curve_fit`, and compare the fitted integrated intensity with the direct sum. Quote the direct sum as your primary value and the fit as a consistency check; the fit centroid and FWHM are what you use to test whether SiO is kinematically distinct from CO.
- Check the contaminant list from Step 1 against every detected feature before calling it SiO.

## 8. Excitation analysis

Under optically thin LTE with a single excitation temperature, with both lines measured in K km/s in the identical beam and identical velocity interval:

1. Compute upper-level column densities, N_u = (8πkν²)/(hc³A_ul) × W, using your Step-1 A_ul and rest frequencies. Include the background term properly: W here is ∫[J(T_ex) − J(T_bg)] dv with J the Rayleigh–Jeans-equivalent radiation temperature and T_bg = 2.73 K; at Band 7 the correction is modest but not zero, and you should carry it rather than hand-wave it.
2. Solve for T_ex from the two-point ratio: N_u(8)/N_u(7) = (g₈/g₇) exp[−(E₈ − E₇)/kT_ex]. Because ΔE between adjacent J levels of SiO is small compared with the temperatures of interest, this ratio is a *weak* thermometer — map out the sensitivity explicitly by plotting the predicted ratio versus T_ex over 10–300 K and showing where your measured ratio and its error bar land. Where the error bar spans a large T_ex range, quote a range, not a central value. Where one line is a limit, the result is a one-sided bound on T_ex.
3. Compute the total SiO column density, N(SiO) = N_u × Q(T_ex)/g_u × exp(E_u/kT_ex), interpolating Q from the CDMS table at your derived T_ex. Do this for both transitions and confirm they agree — they must, by construction, if you solved for T_ex correctly; disagreement means an arithmetic error.
4. Compute a CO 3–2 integrated intensity in the same aperture and intervals as a *kinematic and relative* reference only. CO 3–2 in these regions is almost certainly optically thick, and the ACA 7 m data have no total-power complement, so extended CO emission is spatially filtered. State both facts where you first use CO. Report N(SiO)/W(CO) as a proxy ratio in explicitly stated units, not as an abundance.
5. State the assumption set in one paragraph in the thesis, with its failure modes named: optically thin SiO, single T_ex for both transitions, uniform beam filling identical for both transitions (this cancels in the ratio only if the emitting region is the same for both — which the matched-beam construction makes plausible but does not prove), LTE level populations, and no blending.

**Uncertainty propagation.** Do it by Monte Carlo, not by analytic error propagation: draw W for each line from a Gaussian with the measured σ_W (truncated at zero), draw the flux-calibration factor per tuning from a 10% Gaussian with the correlated/uncorrelated split determined in Step 4.5, propagate each draw through Steps 8.1–8.3, and report the 16th/50th/84th percentiles of T_ex and N(SiO). For limit cases, sample the one-sided constraint. 10⁴ draws is plenty.

## 9. The comparative tests

Three specific tests, each stated as a hypothesis before you look:

1. **Is SiO kinematically distinct from CO?** Per aperture, compare the SiO and CO 3–2 line centroids and FWHMs, and compare the fraction of each line's integrated intensity falling in the high-velocity interval. Plot the normalized SiO and CO profiles overlaid for all apertures in a single multi-panel figure — this figure is the visual heart of the thesis.
2. **Is high-velocity SiO more excited than low-velocity SiO?** Within each source, compute T_ex and N(SiO) separately in the low- and high-velocity intervals of the same aperture and difference them. Because the two intervals come from the same cubes, same beam, and same calibration, most systematics cancel; this is your cleanest internal comparison, and you should say so.
3. **Do SiO properties track outflow velocity extent?** Rank the seven sources by the self-measured CO v_max from Step 6.3 and test for a monotonic trend in T_ex, N(SiO), and N(SiO)/W(CO) with a Spearman rank correlation, bootstrapping over the Monte Carlo realizations from Step 8 to get the distribution of ρ and p. With seven points (fewer, if a source drops out at Step 2), report ρ, its bootstrap interval, and p, and let the numbers speak — do not fit a line through seven points with large error bars and quote a slope.

Where distances enter — any conversion of angular scale to AU, or of column density to mass — adopt literature distances, cite each one individually in the table, and mark every distance-dependent quantity in the results tables with a symbol. The data description characterizes these sources only as "within a few hundred pc," so all headline results are framed as distance-independent line ratios and excitation temperatures.

## 10. Products, reproducibility, and pacing

Keep everything in one git repository: a pinned CASA version, one numbered script per workflow stage (download/audit → uvcontsub → imaging → homogenization → aperture extraction → measurement → excitation → figures), a machine-readable table of aperture positions, and the derived-quantities table as CSV. The homogenized 5″ common-beam FITS cubes and moment maps, the aperture spectra, and the T_ex / N(SiO) / N(SiO)–CO table constitute the deliverable. Every figure should regenerate from the CSVs with a single script.

A workable pace: Steps 1–2 in the first three to four weeks (the audit will take longer than you expect and will surface at least one of the coordinate, naming, or window-edge problems above); Steps 3–4 through mid-semester, with the homogenization validated on one source end-to-end before you touch the other six; Steps 5–7 as a single push once the pipeline is scripted, since it then runs per-source in minutes; Steps 8–9 and writing in the final third. Build the whole chain on one bright, well-behaved source first — BHR 71 and HH 212 both have among the better line sensitivities in the table — and only then run all seven through the identical script. If you find yourself doing anything by hand for the second source that you did by hand for the first, stop and script it.
