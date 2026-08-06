## 0. Working environment and reproducibility scaffolding

Set this up before you touch data, because everything downstream is a rerun of it.

Create a git repository with the layout `data/` (raw archive tarballs, never edited), `products/` (derived cubes, moments, model fits), `code/`, `catalogs/`, and `figs/`. Pin your software: one CASA version (record the exact build string in the README and use it for every task in this project — do not mix versions between the QA2 restore, the imaging checks, and the injection tests), plus a Python environment file listing `astropy`, `spectral-cube`, `radio-beam`, `astroquery`, `numpy`, `scipy`, `lmfit` (or `emcee`), `photutils`, and `matplotlib` with versions.

Every per-target parameter — OUS UID, beam, channel width, mosaic flag, adopted mask thresholds, aperture centroid, final systemic velocity — lives in a single machine-readable configuration file (`targets.yaml` or an ECSV table), not in scripts. Analysis scripts read that file and write to `products/`. Drive the whole thing from a `Makefile` or `snakemake` workflow so that "rerun target X end-to-end" is one command. Fix and record all random seeds used in the injection work of §4. This is what makes the injection–recovery calibration meaningful: the synthetic sources must pass through byte-identical code paths as the real galaxies, and that only holds if the pipeline is scripted rather than hand-driven.

## 1. Retrieval and inventory of the 20 OUSs

Query the ALMA Science Archive for project code `2018.1.00473.S` using `astroquery.alma` (or the web interface at almascience.nrao.edu/aq), and download all 20 member OUSs listed in the data description, requesting both the pipeline-calibrated measurement sets and the QA2 image products. Verify you have 20 OUS × 1 science target each, matching the UIDs `uid://A001/X133d/X1bd2` through `X1c1e`. Untar into `data/<uid>/` and checksum.

For each target, run `listobs` on the calibrated MS and record: number of pointings (this is your independent check on the mosaic flag — the description lists five mosaics, `X1bd2`, `X1be6`, `X1bea`, `X1bf2`, `X1c1e`, and fifteen single pointings), integration time, spectral-window setup and observed frequency coverage, and the antenna configuration (these are stand-alone ACA 7-m data; confirm no 12-m antennas and note whether any total-power product is present in the delivery, which the data description does not list).

For each QA2 cube, read the header and tabulate: restoring beam BMAJ/BMIN/BPA (the description quotes 4.9–6.7″ across the sample), pixel scale and pixels-per-beam, channel width in km/s (~5.1–5.3), number of channels, observed frequency of the first and last channel, velocity frame and definition (radio vs. optical, LSRK vs. barycentric — record this explicitly; you will need it for §2), and whether the delivered image is primary-beam-corrected or flat-noise. Put all of this in `catalogs/inventory.ecsv`. This table is a deliverable in its own right and is the first thing your reader will want.

## 2. Line verification and systemic velocities — do this before any physical conversion

The data description quotes CO J=2–1 at a **rest** frequency of 230.538 GHz and flags its line list as generated from general knowledge and requiring verification. So verify it: query Splatalogue for ¹²C¹⁶O J=2–1 and record the tabulated rest frequency with its reference in your README. Do the same for ¹³CO(2–1) (~220.399 GHz), C¹⁸O(2–1) (~219.560 GHz), and the CN N=2–1 hyperfine complex (~226.66/226.87 GHz), and confirm for each target's own observed window that none of these falls in band at that target's redshift. Document the check; do not assume it.

The redshifts in the data description (roughly z ≈ 0.013–0.047 across the sample; e.g. z≈0.040 for J132443.68+323225.0 from its 220.7–222.7 GHz tuning, z≈0.017 for J132051.75+312159.8 from its 225.7–227.7 GHz tuning) are **back-derived from the band centers, not measured**. Treat them only as starting guesses for where to look for the line. Your own systemic velocities come from the data: extract an integrated spectrum per target (§3), fit the line centroid, convert the centroid observed frequency to a redshift using the verified rest frequency and the header's velocity convention, and adopt *that* as the target redshift. Carry both columns in the final catalog — `z_tuning_inferred` (from the description, labeled as assumed) and `z_measured` (yours) — and use only the measured one for distances.

Convert measured redshift to luminosity and angular-diameter distance with `astropy.cosmology.FlatLambdaCDM`, stating your adopted H₀ and Ω_m explicitly in the paper and config file. At these redshifts the choice barely matters, but it must be stated once and used everywhere. From the angular-diameter distance compute each target's kpc/arcsec scale and its beam size in kpc; that number governs §3–§5.

## 3. Cube preparation, moment maps, and spectra — one recipe for all 20

The QA2 cubes are your primary imaging products. Do **not** blanket re-image.

For each cube: (i) apply primary-beam correction with `impbcor` using the delivered `.pb` image if the delivery is flat-noise, and keep both the flat-noise and pb-corrected versions — flat-noise for masking and noise estimation, pb-corrected for photometry and fitting; (ii) measure the noise in signal-free channels with `imstat` on the flat-noise cube, using a robust (median-absolute-deviation) estimator, and record σ per channel.

Build masks with a single **smooth-and-mask** recipe applied identically to all 20: convolve the flat-noise cube spatially to twice the restoring beam with `imsmooth` and spectrally by a 3-channel Hanning-like kernel; define high-confidence seeds at ≥4σ in the smoothed cube requiring 2 adjacent channels; dilate those seeds into a ≥2σ envelope; require the final mask to have at least one beam area of contiguous pixels per channel. Fix these thresholds once, at the start, and record them in the config — resist the urge to tune them per galaxy, because a per-galaxy mask destroys the homogeneity that is the point of the atlas. If a specific target demonstrably fails (e.g. no seed pixels at all), record it as a non-detection under the fixed recipe rather than lowering the threshold.

From the masked cube produce, with `immoments`: moment-0 (integrated intensity, Jy beam⁻¹ km s⁻¹) and moment-1 (intensity-weighted velocity), both on the pb-corrected cube, plus a moment-0 uncertainty map propagated from σ and the number of masked channels per pixel. Extract the integrated spectrum by summing the pb-corrected cube over a generous fixed aperture (§4 refines this), converting Jy beam⁻¹ to Jy using the beam area in pixels.

**QA gate.** Inspect every moment-0, moment-1, and spectrum by eye against a written checklist: residual imaging artifacts (stripes, negative bowls comparable to the source), missing or incorrect pb correction, obviously wrong beam in the header, line emission running into a band edge. Only a target that *fails a stated check* gets re-imaged in `tclean` — and then you re-image with parameters recorded in the config (`gridder='mosaic'` for the five mosaicked targets, `'standard'` otherwise; `specmode='cube'`, natural or Briggs weighting matched to the QA2 choice, a clean mask from the smoothed cube, threshold ~2σ), and you write a short case note in the repository explaining what failed and what changed. Expect this to apply to a small minority of targets.

## 4. Leg A — fluxes, line widths, systemic velocities, rotation amplitudes

These are the sample-wide results; they exist for all 20 targets regardless of how the size fitting turns out.

**Total flux by growth curve.** On the pb-corrected moment-0 map, place elliptical apertures centered on the CO centroid, with the position angle and axis ratio initially from a second-moment (image-moment) estimate of the emission, and grow the semi-major axis in steps of ~0.25 beam out to well beyond the visible emission. Plot cumulative flux versus aperture radius. Identify the plateau as the radius beyond which successive increments are consistent with zero within the local noise over three consecutive steps; adopt the plateau value as S_CO Δv in Jy km s⁻¹. Take the flux uncertainty from the growth curve itself — the scatter of the cumulative flux across the plateau region, added in quadrature with the propagated moment-0 noise inside the adopted aperture — and add the ALMA Band 6 absolute flux-calibration uncertainty as a separate, clearly labeled systematic column (do not fold it into the statistical error). For mosaics, restrict apertures to the region where the primary-beam response exceeds a fixed threshold (0.2–0.3) and record which targets are affected.

Convert flux to CO(2–1) luminosity L′_CO(2–1) with the standard Solomon & Downes relation using your measured redshift and luminosity distance. Report L′ in K km s⁻¹ pc²; if you also quote an H₂ mass, state the adopted α_CO and R21 assumption explicitly as assumptions, not measurements.

**Systemic velocity and line widths.** From the aperture-integrated spectrum, measure W50 and W20 by the standard two-horn method: find the peak on each side of the profile, interpolate the velocity at which the flux crosses 50% (and 20%) of each side's peak, and take the difference; take v_sys as the midpoint of the W50 crossings. Cross-check against a Gaussian or Busy-function fit and report the difference as part of the uncertainty. Estimate uncertainties by Monte Carlo: add noise realizations at the measured per-channel σ to the observed spectrum and repeat the measurement several hundred times.

**Rotation amplitude.** Apply a uniform admission test: a galaxy enters the kinematic subsample only if its moment-1 map shows a monotonic velocity gradient spanning **≥3 independent beams**. Compute the number of independent beams across the emission from the beam and the moment-0 extent; record pass/fail for all 20. For those that pass, determine the kinematic major-axis position angle either by fitting a tilted-ring or simple rotating-disk model to moment-1, or by maximizing the velocity gradient over trial PAs — pick one method and apply it uniformly. Extract a position–velocity cut along that axis with `impv`, using a slit width of one beam. Measure the projected rotation amplitude from the PV envelope: at each position offset, take the velocity at which the emission falls to a fixed fraction (e.g. 20%) of the local peak on the high- and low-velocity sides, and adopt half the difference between the flat outer plateaus on the two sides as V_rot·sin(i)_obs. Quote this as an **observed, inclination-uncorrected** value for every galaxy in the kinematic subsample.

## 5. Leg B — image-plane forward modeling of an inclined exponential disk

Fit each pb-corrected moment-0 map with an inclined exponential disk. The model is I(r) = I₀ exp(−r/h) evaluated on an elliptical radial coordinate with free parameters: central surface brightness I₀, scale length h, axis ratio q = b/a, position angle PA, and centroid (x₀, y₀). Generate the model on a pixel grid oversampled by ~3–5× relative to the image pixels, convolve with that target's restoring beam (build the kernel from BMAJ/BMIN/BPA in the header — use each target's own beam, never a sample-average beam), rebin to the image grid, and for the five mosaics multiply by the primary-beam response pattern before comparison if you are fitting the flat-noise map, or fit the pb-corrected map with a pb-derived noise map. Minimize χ² in the image plane.

Two things you must get right in the likelihood. First, the noise in an interferometric image is **correlated on the beam scale**, so the effective number of independent measurements is the number of *beams* in the fitting region, not pixels; scale your χ² (or the uncertainties) by the pixels-per-beam factor, and state the scaling you used. Second, define the fitting region once and identically for all targets — a fixed multiple of the growth-curve plateau radius, masked to exclude any unrelated emission.

Optimize first with `scipy.optimize.least_squares` from several starting points to avoid local minima, then run `emcee` (or `lmfit`'s MCMC) from the best fit to get posteriors on h, q, and PA, since these three are strongly covariant when the source is only marginally resolved. Report medians and 16th/84th percentiles. Convert h from arcsec to kpc with the §2 angular scale.

This approach is chosen over `uvmodelfit` deliberately, and you should say so in your methods chapter: `uvmodelfit` offers no exponential component, assumes a single phase center (so it cannot handle the five mosaicked targets `X1bd2`, `X1be6`, `X1bea`, `X1bf2`, `X1c1e`), and fits per channel rather than the line-integrated emission. Image-plane forward modeling treats mosaics and single pointings identically and works on one velocity-collapsed map. Its cost is that interferometric spatial filtering is not handled natively — which is exactly what §6 measures.

## 6. Calibration by uv-plane injection and image-plane recovery

This is the step that converts §5 from "fitted numbers" into "numbers with a known floor," and it is the core of Leg B. Budget real time for it.

Pick **two** representative targets from the inventory table: one near the best combination of beam size and line sensitivity, one near the worst (use the tabulated angular resolutions, 4.9–6.7″, and line sensitivities, ~5.6–10.7 mJy beam⁻¹ at 10 km s⁻¹, to justify the choice in writing). Work on *copies* of their calibrated measurement sets.

For each synthetic source: build a FITS model image of an inclined exponential disk with known h, q, and total flux, placed at a sky position offset from the real galaxy by enough to avoid overlap but still well inside the primary beam (record the offset), and given the same spectral profile shape as the real target's integrated spectrum so the velocity-collapse step behaves identically. Use `ft` to Fourier-transform that model image into the MODEL_DATA column of the MS copy, then add MODEL_DATA into DATA so the synthetic disk carries the *real* uv coverage and the *real* noise of that target. (`simobserve` with the real MS as an antenna/pointing template is an acceptable alternative path; whichever you use, use it for every realization.) Then image the modified MS with `tclean` and push the result through the **identical** §3 masking/moment calls and the **identical** §5 fitting call — no per-realization tuning, no eyeball intervention.

Grid: ~5 scale lengths (spanning from well below to a few times the beam), × 3 total fluxes (bracketing the observed sample's range), × 2 inclinations (one near face-on, one appreciably inclined), × 2 targets ≈ 60 realizations. Script it and run it in batch.

Three outputs, each a figure and a table column:

1. **Minimum recoverable scale length** as a function of S/N and of h/θ_beam — defined operationally, e.g. the smallest input h at which the recovered h is unbiased at the ≤20% level and its posterior excludes the unresolved case. This is your size floor.
2. **Axis-ratio bias** — recovered q versus input q as a function of size and S/N. This determines which galaxies are allowed a deprojection in §8.
3. **Fractional flux loss** as a function of source size relative to each target's shortest-baseline limit, which quantifies how much extended emission the ACA-only configuration filters out for a source of a given extent.

Apply the results as a hard rule: quote a scale length only for galaxies above the measured floor; every galaxy below it gets an upper limit on h derived from the injection grid at that galaxy's S/N.

## 7. Largest recoverable scale, per target

For each MS, read the UVW column and build the baseline-length distribution in kλ at the observed CO(2–1) frequency. Take a robust shortest-baseline measure (e.g. the 5th percentile of baseline lengths, not the single shortest, which is noise-sensitive) and compute the maximum recoverable scale from the standard θ_MRS ≈ 0.6 λ/L_min relation; state the coefficient and its source. Tabulate θ_MRS per target in arcsec and in kpc.

Then flag any galaxy whose fitted scale length (or growth-curve plateau radius) approaches a fixed fraction of its own θ_MRS — say, exceeds one-third of it — as potentially flux-compromised, and combine that flag with the §6 flux-loss curve to state how much flux such a source could plausibly be missing.

State plainly in the methods chapter that these are 7-m-array-only data with no total-power product listed in the delivery, and that the JCMT single-dish CO(2–1) fluxes that originally selected these targets are not part of this data description, so the usual external single-dish flux-recovery comparison is unavailable; this internal shortest-baseline bound plus the §6 injection curve substitutes for it.

## 8. Inclination handling

The §5 fit is inclined: q and PA are free parameters, so the resolved subset gets photometric inclinations, and scale lengths for that subset are deprojected using the fitted q (with an assumed intrinsic thickness, stated explicitly, when converting q to i).

Two consequences to carry through the catalog without exception:

- For galaxies **below** the §6 size floor, q is unconstrained. Their scale-length upper limits are computed and labeled as **face-on-equivalent** and flagged as such in a dedicated catalog column.
- Rotation amplitudes and line widths are reported **twice**: as observed, inclination-uncorrected values for all 20 targets, and additionally deprojected (dividing by sin i from the fitted q) **only** for galaxies where §6 shows q is recovered without significant bias at that galaxy's size and S/N. The deprojected values are catalog columns for future use; no CO Tully–Fisher calibration is fitted or claimed from them.

## 9. Products, catalog, and figures

Assemble `catalogs/jingle_aca_co21.ecsv` (also written to FITS) with one row per target and, at minimum, these columns with units and per-column descriptions: OUS UID; target name; RA, Dec; beam BMAJ/BMIN/BPA; channel width; mosaic flag; z_tuning_inferred (labeled assumed) and z_measured; adopted distance and kpc/arcsec scale; S_CO Δv with statistical and calibration uncertainties; L′_CO(2–1); v_sys; W50 and W20 observed; V_rot·sin(i)_obs and kinematic-subsample flag; fitted h with uncertainties **or** face-on-equivalent upper limit, with a flag distinguishing the two; fitted q and PA with uncertainties where valid; deprojected h, W50, and V_rot where §8 permits; θ_MRS in arcsec and kpc plus the flux-compromise flag; and a per-target note field recording any re-imaging from §3.

Build the atlas as one uniform page per target: moment-0 with the growth-curve aperture and beam drawn, moment-1 with the kinematic major axis drawn, the PV cut, and the integrated spectrum with W50/W20 and v_sys marked. Same stretch convention, same panel layout, same beam-in-corner placement for all 20.

Produce the size–luminosity figure — fitted h (or upper limit, drawn as an arrow) versus L′_CO(2–1) — with points color-coded by measured redshift, and overplot the §6 size floor translated into kpc at each redshift so the distance-dependent resolution bias is visible on the figure rather than buried in the text. State up front, when you present it, that the sample is the 20 *brightest* JINGLE targets in JCMT CO(2–1) and is therefore selection-compressed in CO luminosity.

## 10. Optional continuum stack, if time remains

If the schedule allows after §1–§9 are complete: for each target, identify line-free channels from the §3 mask (excluding a generous buffer around the emission), and image continuum with `tclean` in `specmode='mfs'` on those channels. Measure the flux or 3σ limit at the CO centroid position in each target. Stack by taking the inverse-variance-weighted mean of the per-target central-pixel measurements, using the per-target continuum sensitivities (~0.34–0.66 mJy beam⁻¹ as tabulated) for the weights, and estimate the stack uncertainty by bootstrap over targets and by stacking at random offset positions as a null test.

If you do this, state the interpretation limit in the same paragraph as the result: because the targets sit at different measured redshifts, the stack averages *different rest-frame wavelengths* around ~1.2 mm across a heterogeneous sample, so it constrains a sample-mean flux, not a well-defined single-wavelength dust measurement.

## 11. Suggested sequencing for one semester

Weeks 1–3: environment, download, inventory table, Splatalogue verification. Weeks 3–6: masking recipe fixed, moments and spectra for all 20, QA gate and any case-by-case re-imaging. Weeks 5–9: Leg A — growth-curve fluxes, line widths, systemic velocities, kinematic admission test and PV rotation amplitudes; the catalog's Leg A columns are complete and frozen at this point. Weeks 8–12: §5 fitting machinery built and run on all 20; §7 θ_MRS computed. Weeks 10–14: §6 injection–recovery grid, then apply its floor to convert §5 outputs into sizes-or-limits and decide which galaxies earn a deprojection. Weeks 13–16: atlas figures, size–luminosity figure, catalog finalization, repository cleanup and README, write-up. Start §6 early enough that the grid can be rerun once — you will almost certainly want to widen the size range after seeing the first pass.
