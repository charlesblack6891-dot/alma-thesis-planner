**Step 1: Data acquisition and preparation**

Log in to the ALMA Science Archive and query project code 2017.1.00379.S. Download only the three Band 6 member OUS products needed for this project: `uid://A001/X1273/Xb4b` (0.237″), `uid://A001/X1273/Xb4d` (0.8″), and `uid://A001/X1273/Xb4f` (4.352″). Each of these covers the same four spectral windows (249.0–250.8, 250.7–252.6, 262.8–264.7, 264.6–266.4 GHz), so HCN(3–2) (rest 265.886 GHz, observed ~263.4 GHz) and HCO+(3–2) (rest 267.558 GHz, observed ~265.1 GHz) are both present in every download. Retrieve the pipeline-calibrated measurement sets and the QA2 image cubes for each. Verify the line identifications against Splatalogue before proceeding, confirming rest frequencies and checking for possible line blending within the ±5 km/s channel width given NGC 3256's z ≈ 0.0093.

For each of the three MOUS, use CASA (matching the pipeline version noted in the QA2 weblog for that MOUS) to re-run `tclean` on the calibrated visibilities for the two spectral windows containing HCN(3–2) and HCO+(3–2), rather than relying solely on the delivered QA2 cubes. Use consistent imaging parameters (Briggs weighting with a fixed robust parameter, common pixel size relative to the beam, matched velocity channel width of 4.424 km/s as delivered) across the two lines within a given MOUS so that the resulting cubes share a common synthesized beam and channelization. Apply the pipeline's primary-beam correction. Inspect each cube for spatial and spectral extent of line emission and confirm the noise level in line-free channels matches the archive-quoted sensitivity (~0.5–6.3 mJy/beam depending on resolution).

**Step 2: Moment maps and detection masking (4.352″ and 0.8″ cubes)**

For each of the two lower-resolution cubes, independently:

- Estimate the RMS noise per channel from line-free channels.
- Generate a integrated-intensity (moment-0) map of HCN(3–2) by summing signal channels, using a fixed signal-to-noise threshold (e.g., 3σ per channel, summed over channels showing contiguous signal — a standard "masked moment" approach, using CASA's `immoments` with a mask derived from a smoothed, thresholded version of the cube to avoid noise bias).
- Apply the identical spatial mask (derived from the HCN map) to the HCO+ cube at the same channels to produce a matched moment-0 map, so that both maps are evaluated over the same pixel/velocity footprint.
- Divide the HCN moment-0 map by the HCO+ moment-0 map pixel-by-pixel only where both maps have a detection above the shared noise cutoff; mask (blank) all other pixels rather than extrapolating a ratio from a non-detection.
- Propagate flux uncertainties into the ratio map (standard error propagation for a ratio of two noisy quantities) and produce a companion "ratio uncertainty map" alongside the ratio map itself.

Because HCN(3–2) and HCO+(3–2) come from the same MOUS and same tuning, they share an identical synthesized beam at each resolution, so no additional convolution or regridding between lines is needed within a given cube.

**Step 3: Kinematic separation of outflow vs. disk gas**

Using the HCN(3–2) cube at each resolution, extract the observed velocity field (e.g., an intensity-weighted mean velocity, or moment-1 map, computed with the same masking as Step 2) and identify the large-scale kinematic (merger/disk) axis directly from this observed field — do not fit a rotation model. Construct a position–velocity (PV) diagram by cutting a slice along this axis with CASA's `impv` task, for both HCN and HCO+.

Define outflow-associated emission operationally using two joint criteria applied directly to the cube: (a) velocity channels offset by more than a fixed threshold (set using the PV diagram and the ~2800 km/s systemic velocity, following the offset used in the PI's proposal/prior outflow literature on NGC 3256) from systemic velocity, and (b) spatial pixels offset from the main emission ridge/disk seen in the moment-0 map. Flag pixels satisfying both criteria as "outflow"; flag pixels near systemic velocity and on the main ridge as "disk." Do this separately, but with the same fixed velocity/spatial thresholds, for both the 4.352″ and 0.8″ cubes.

**Step 4: Ratio comparison, disk vs. outflow**

For each resolution independently, compute the mean (and standard deviation) of the pixel-by-pixel HCN/HCO+ ratio map (from Step 2) separately within the outflow mask and within the disk mask (from Step 3). Compare the two distributions (e.g., with a simple two-sample statistical test, such as a Mann-Whitney U test given likely non-Gaussian pixel distributions) to determine whether the outflow gas shows a statistically distinguishable HCN/HCO+ ratio relative to disk gas, at each resolution. Report the ratio contrast (outflow mean / disk mean) and its uncertainty for both the 4.352″ and 0.8″ datasets, and check for consistency between the two independent resolutions as an internal cross-check.

Frame this ratio explicitly as a proxy for chemistry/excitation conditions (ionization balance, shock/AGN vs. gravitational-compression chemistry), not as a density or kinetic-temperature measurement, and note where the result does or does not support enhanced HCN/HCO+ in outflowing gas relative to disk gas. Separately, compare the spatial and velocity extent of the outflow-flagged emission against the outflow geometry described in the PI's proposal, and note in the written discussion whether any velocity-offset emission is plausibly tidal debris (common in a late-stage merger like NGC 3256) rather than outflow — this is a qualitative comparison to the literature, not an independent kinematic decomposition.

**Step 5: Clump identification at high resolution (0.237″ cube)**

Using the 0.237″ HCN(3–2) cube, restrict attention to velocity channels flagged as "outflow" in Step 3 (using the same fixed velocity threshold, reapplied at this resolution). Visually and quantitatively (peak S/N per channel or in the moment-0 map restricted to outflow velocities) identify 3–5 discrete, compact emission peaks ("clumps") that stand clearly above the local noise. Cross-check that the same positions show corresponding HCO+ emission in the matching HCO+ cube at this resolution.

For each identified clump:

- Extract a sub-cube centered on the clump position.
- Fit a 2D Gaussian to the clump's spatial emission in the moment-0 map (or in the peak channel) using CASA's `imfit`, fitting both HCN and HCO+ independently.
- Deconvolve the fitted Gaussian size from the synthesized beam (`imfit` reports the deconvolved size and its uncertainty directly). Given that 0.237″ corresponds to tens of parsecs at NGC 3256's distance, expect several clumps to be only marginally resolved; when the deconvolved FWHM is not statistically distinct from zero (i.e., fitted size does not exceed the beam within its uncertainty), report only an upper limit on the true source size, using the beam size as that upper limit.
- Extract a 1D spectral line profile at each clump position (spatially integrated over the fitted clump aperture) and fit a single Gaussian (or, if visibly non-Gaussian, note this and fit the FWHM directly from the profile) to obtain the velocity linewidth (FWHM) and its uncertainty.

**Step 6: Size–linewidth relation and virial mass estimates**

Using the fitted (or upper-limit) clump sizes and linewidths from Step 5, compute, for each clump, an order-of-magnitude virial mass estimate using the standard virial mass formula for a self-gravitating cloud, M_vir ≈ f × R × Δv², where R is the deconvolved (or upper-limit) radius, Δv is the fitted linewidth, and f is a standard geometry-dependent virial coefficient taken from the literature. Explicitly propagate the size uncertainty (or upper limit) through to the mass estimate, and report all masses (or mass limits) as order-of-magnitude estimates given the marginal resolution of the beam relative to clump size. Where only a size upper limit exists, report the corresponding virial mass as a lower limit, and state this bound as a valid result rather than treating it as insufficient information.

Plot (if sufficient clumps have resolved, non-limit sizes) size versus linewidth for the clump sample, and compare qualitatively to established size–linewidth relations for Galactic and extragalactic molecular clouds, noting where clumps sit relative to this reference relation.

**Step 7: Local ratio comparison at clump scale**

For each clump position/aperture identified in Step 5, compute the local HCN/HCO+ ratio (using the same masked, matched-beam moment-0 maps constructed for that MOUS, following the Step 2 procedure but evaluated only over the clump aperture rather than the full outflow mask). Compare each clump's local ratio to the global outflow-vs-disk ratio contrast measured in Step 4 (using the 0.8″ cube result as the nearest-resolution point of comparison, since the 0.237″ cube alone does not have the S/N or field coverage for a full disk map). Note whether individual clumps that show line-ratio enhancement also correspond to marginally resolved (i.e., high-density, small-size) clumps, as this would be the observational signature expected under the compression hypothesis being tested.

**Step 8: Synthesis and presentation**

Assemble the final set of deliverables: (1) HCN(3–2)/HCO+(3–2) ratio maps with uncertainty maps at 4.352″ and 0.8″ resolution; (2) PV diagrams along the kinematic axis for both lines; (3) the disk-vs-outflow ratio contrast and its statistical significance at both resolutions; (4) a table of clump positions, fitted or upper-limit sizes, linewidths, and virial masses (or mass limits) from the 0.237″ data; (5) a size–linewidth plot where applicable; and (6) a table comparing local clump-scale ratios to the global outflow ratio. Present all results as a first-order chemical and kinematic diagnostic of the outflow, explicitly distinguished in the thesis text from the PI's full three-rung HCN/HCO+ LVG density and kinetic-temperature analysis, which this project does not attempt to reproduce.
