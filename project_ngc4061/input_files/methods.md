**1. Preliminary calculation (Week 1, before touching the cube)**

Before opening any data, compute the black hole's sphere of influence using the values already reported in Nguyen et al. 2026: r_SOI = GM_BH/σ². Using M_BH ≈ 1×10⁹ M_sun and the paper's reported stellar velocity dispersion range (σ ≈ 200–300 km/s), tabulate r_SOI in parsecs and convert to angular size at D = 107.2 Mpc. Compare this directly to the 0.16″ synthesized beam (≈83 pc at this distance). Record the ratio SOI/beam (≈0.6–1.3) in the thesis methods section as a stated, load-bearing fact that governs the rest of the analysis plan — not as a result to be "discovered" later. This calculation requires only a calculator/Python and the numbers already in the data description; it sets expectations for both possible fiducial outcomes described below.

**2. Data preparation**

- Obtain the calibrated 12CO(2-1) cube, the Band 6 continuum image, and the three moment maps (0, 1, 2) as delivered data products; do not recalibrate the raw visibilities.
- In CASA (or a Python equivalent using spectral-cube/astropy), inspect the cube's header for pixel scale, spectral axis (convert channel to velocity using the redshifted 230.538 GHz line and NGC 4061's systemic velocity from the moment-1 map), and beam parameters.
- Apply the primary-beam correction to the cube if not already applied in the delivered product, since BBarolo fits require PB-corrected flux for a correct mass normalization.
- Construct a signal mask (e.g., using a dilated-mask or sigma-clipping approach in spectral-cube) to exclude noise channels outside the CO disk before fitting, and re-derive moment maps from the masked cube as a consistency check against the supplied moment maps.
- Measure the continuum peak pixel position and its centroid uncertainty (from the 120 μJy/beam rms and the continuum beam) — this becomes the fixed dynamical center for all subsequent fits.

**3. Fiducial tilted-ring fit with 3D-Barolo (Semester 1)**

- Install and configure 3D-Barolo (BBarolo), which fits tilted-ring models directly to the observed cube with built-in 3D convolution by the CASA-derived synthesized beam, avoiding any need to write custom beam-smearing code.
- Set up the BBarolo parameter file (`BB.par`) with: the continuum-peak position fixed as the kinematic center (XPOS, YPOS held fixed, not free parameters); initial guesses for systemic velocity (from the moment-1 map), position angle and inclination (from the moment-0 morphology and moment-1 velocity field), and ring width set to roughly the beam FWHM (≈0.16″) to avoid oversampling independent resolution elements.
- Run BBarolo in 3DFIT mode, allowing rotation velocity, position angle, and inclination to vary ring-by-ring while the center and systemic velocity remain fixed (or fixed after an initial free pass confirms consistency with the moment-1 systemic velocity).
- Iterate on the number and width of rings, and on the mask (using the same signal mask from Step 2) until the fit converges to a stable rotation curve — i.e., ring-to-ring parameters vary smoothly rather than oscillating, and the residual cube (data minus model, produced natively by BBarolo) shows no strong coherent large-scale residual pattern beyond expected noise.
- Convert the converged rotation curve in the innermost rings (within or near the SOI) into an enclosed dynamical mass, using the fixed stellar mass profile from Nguyen et al. 2026 (adopted, not re-derived) to isolate the black hole's contribution to the central rise in circular velocity.
- Document explicitly which of the two pre-declared outcomes occurred: (a) the fit converges on a stable inner rotation curve consistent with the published M_BH within its errors, or (b) the fit cannot uniquely resolve the inner rotation curve at this resolution (e.g., ring parameters near the center are degenerate or poorly constrained), in which case report a bounding range for M_BH consistent with the data rather than a point estimate. Either outcome is a complete, reportable semester-1 deliverable.
- Inspect the residual maps for signatures of warps, non-circular motion, or lopsidedness in the disk, and note these qualitatively as part of the fit-quality assessment (not as a new science claim).

**4. Single-axis systematics check (Semester 2)**

- Read the error budget and systematics section of Nguyen et al. 2026 to enumerate which sources of uncertainty they already quantified (e.g., choice of dynamical center, inclination, mass-to-light ratio, PSF model).
- Select exactly one systematic not already covered by their published error budget — either (a) ring-width/geometry choice (re-running the fiducial BBarolo fit with a coarser and a finer ring width than the fiducial setup) or (b) inclusion versus exclusion of channels/regions showing elevated velocity dispersion or non-circular motion in the moment-2 map (re-masking the cube to exclude these regions and re-running the identical fit).
- Re-run the BBarolo fit under this single alternate configuration, holding all other choices (fixed center, systemic velocity, stellar mass profile) identical to the fiducial run.
- Compare the resulting M_BH (or bound) to the fiducial value from Step 3, quantifying the shift as the systematic's contribution to the overall uncertainty.

**5. Final comparison and write-up**

- Tabulate: the published M_BH from Nguyen et al. 2026, the thesis's fiducial BBarolo result (point estimate or bound), and the result under the single alternate systematic configuration.
- Present the SOI/beam ratio from Step 1 alongside these results to explain, quantitatively, why the fit produced a point estimate or a bound.
- Frame the final result explicitly as an independent, second-pipeline verification of a published dynamical mass measurement, using the continuum image as an independent positional anchor and BBarolo as a methodologically distinct fitting tool from whatever approach Nguyen et al. 2026 used, rather than as a search for a new or revised black hole mass.
