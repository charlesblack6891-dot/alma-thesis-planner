# Mapping the HCN/HCO+(J=3–2) Line Ratio and Clump Properties in the NGC 3256 Outflow

## Abstract

This thesis tests whether outflowing dense gas in the late-stage merger NGC 3256 carries a chemical signature consistent with compression-driven star formation, using archival ALMA Band 6 data from project 2017.1.00379.S (three Band 6 member OUS at 4.352″, 0.8″, and 0.237″ resolution) that simultaneously cover HCN(3–2) and HCO+(3–2). Working at each cube's native, shared-beam resolution, the project builds masked moment-0 maps and HCN/HCO+ ratio maps, defines outflow versus disk gas from the observed velocity field and a position–velocity diagram using a literature-standard offset from the ~2800 km/s systemic velocity, and tests whether the outflow ratio is enhanced relative to disk gas at two independent resolutions. At the highest resolution, 3–5 discrete outflow clumps are identified and their sizes, linewidths, and order-of-magnitude virial masses (or bounding limits, where marginally resolved) are measured and compared to the global ratio contrast. Throughout, the ratio is treated explicitly as a proxy for chemistry/excitation conditions — not a density or temperature measurement — complementary to, rather than a replacement for, the PI's full three-rung HCN/HCO+ LVG density analysis.

## Work Plan

**Acquisition & imaging:** Download pipeline-calibrated visibilities and QA2 cubes for the three member OUS (Xb4b 0.237″, Xb4d 0.8″, Xb4f 4.352″); verify HCN(3–2)/HCO+(3–2) line IDs against Splatalogue at z≈0.0093. Re-image each MOUS's relevant spectral windows in CASA `tclean` with matched Briggs weighting, pixel size, and 4.424 km/s channels so HCN and HCO+ share a common beam per cube; apply primary-beam correction and confirm noise against archive sensitivities.

**Moment maps & ratio (4.352″ and 0.8″, independently):** Estimate per-channel RMS; build masked HCN moment-0 maps (`immoments`, 3σ threshold, smoothed mask), apply the identical mask to HCO+, and divide pixel-by-pixel only where both are detected, blanking non-detections. Propagate flux uncertainties into a companion ratio-uncertainty map. **Key output: ratio maps + uncertainty maps at two resolutions.**

**Kinematic separation:** Derive the observed HCN moment-1 velocity field and kinematic axis directly (no rotation fit); cut PV diagrams along that axis (`impv`) for both lines. Flag "outflow" pixels by fixed velocity offset from systemic plus spatial offset from the main ridge; flag "disk" pixels near systemic/on-ridge, using the same thresholds at both resolutions. **Key output: PV diagrams.**

**Ratio comparison:** Compute mean/SD of the ratio map within outflow vs. disk masks at each resolution; test significance with a Mann–Whitney U test; report the outflow/disk contrast and check consistency across resolutions. Discuss the ratio as a chemistry/excitation proxy and note whether offset emission could plausibly be tidal debris rather than outflow, compared qualitatively to the PI's proposal. **Key output: disk-vs-outflow ratio contrast table with significance.**

**Clump identification (0.237″):** Within outflow-velocity channels, identify 3–5 compact HCN peaks with corresponding HCO+ counterparts. Fit a 2D Gaussian (`imfit`) per clump for deconvolved size (or a beam-based upper limit if unresolved) and fit the 1D line profile for velocity linewidth.

**Size–linewidth & virial mass:** Compute order-of-magnitude virial masses (M_vir ≈ f·R·Δv², literature-standard f), propagating size uncertainties/limits into mass estimates or lower limits. Plot size vs. linewidth where resolved and compare qualitatively to standard Galactic/extragalactic size–linewidth relations. **Key output: clump table (position, size/limit, linewidth, virial mass/limit) and size–linewidth plot.**

**Local ratio comparison:** Compute the local HCN/HCO+ ratio at each clump aperture and compare to the global 0.8″ outflow ratio, checking whether enhanced-ratio clumps coincide with marginally resolved, small/dense clumps — the signature expected under the compression hypothesis.

**Synthesis:** Assemble ratio maps with uncertainties (4.352″, 0.8″), PV diagrams, the disk-vs-outflow contrast, the clump table, the size–linewidth plot, and the local-vs-global ratio comparison, presented as a first-order chemical/kinematic diagnostic distinct from the PI's full LVG density and temperature analysis.

## Background Reading

- N. Harada, K. Sakamoto, S. Martín, S. Aalto, R. Aladro, K. Śliwa (2018), "ALMA Astrochemical Observations of the Infrared-luminous Merger NGC 3256." Same PI and target, but a broader multi-species spectral-scan survey on an earlier, different dataset — relevant background on NGC 3256's chemistry, not a report on this project's data.
