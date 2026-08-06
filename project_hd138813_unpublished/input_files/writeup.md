# Quantitative Radial Dust-Gas Structure in the HD 138813 Debris Disk: A Resolution-Matched Reanalysis Using Public ALMA Data

## Abstract

The HD 138813 debris disk hosts co-located dust and CO gas whose radial relationship has so far only been characterized qualitatively. This thesis uses exclusively public ALMA data — the ARKS Band 7 continuum (project 2022.1.00338.L, released following A&A 705, A195, January 2026) and the CO data of Hales et al. (2019) — to derive independent, resolution-matched radial brightness profiles for dust and gas and compute an uncertainty-bounded gas-to-dust ratio as a function of radius. Before analysis begins, the ARKS survey papers are audited for any existing single-target radial dust-gas comparison for this source: if one exists, the thesis becomes an independent reproducibility check against those published numbers; if not, it proceeds as an original comparison. The proprietary 2025.1.00062.S dataset (released 2027) is excluded entirely. The approach is deliberately bounded to a single target and two already-public tracers, using standard tools (CASA, `frank`/`galario`, or symmetric image-domain azimuthal averaging), so that a well-defined quantitative question — whether the gas-to-dust ratio shows a radial trend, or whether no such trend is detectable at current sensitivity — is answered within a single thesis timeframe.

## Work Plan

**Weeks 1–3 — Literature audit and scope triage.** Read the ARKS survey-overview paper and all nine A&A 705, A195 companion papers, extracting every statement on HD 138813 (resolution, ring geometry, any CO or joint dust-gas result). Cross-reference against Lieman-Sifry et al. (2016) and Hales et al. (2019). This determines whether the thesis is an original analysis or a reproducibility check against a published ARKS result; the decision and justification are documented in the methods chapter.

**Weeks 3–4 — Data acquisition and inventory.** Query the ALMA archive for 2022.1.00338.L (dust) and the Hales et al. CO project, recording in a data-provenance table which tier of product exists for each tracer (calibrated visibilities vs. only released images/moment maps). Confirm in writing that 2025.1.00062.S is never accessed.

**Weeks 4–7 — Calibration and imaging (where visibilities exist).** For any tracer with retrievable visibilities, image with CASA `tclean` (Briggs robust = 0.5, iterated only if S/N-limited), then fit source geometry (inclination, PA, center) via elliptical Gaussian/ring model, sanity-checked against literature geometry.

**Weeks 7–10 — Radial profile extraction (dual path, applied symmetrically).** *Path A (visibility-domain):* fit non-parametric radial brightness profiles with `frank` directly to deprojected visibilities for each tracer independently, fitting geometry per tracer (a dust-gas misalignment is itself diagnostic) and propagating `frank`'s posterior uncertainties. *Path B (image-domain):* for any tracer with only released images/moment maps, deproject and azimuthally average in elliptical annuli one beam wide, propagating uncertainty from map rms and beams-per-annulus. If tracers use different paths, also compute the Path-B profile for the Path-A tracer to keep the comparison like-for-like.

**Weeks 10–11 — Geometry consistency and common axis.** Compare dust and CO geometries in units of combined sigma; adopt an inverse-variance-weighted common geometry if consistent, otherwise retain separate geometries while still projecting both profiles onto a shared physical (au) axis at 130.3 pc, flagging any disagreement as a result.

**Weeks 11–14 — Quantitative comparison and mass cross-check.** Compute the radius-dependent CO/dust ratio profile with quadrature-propagated uncertainty; test constant vs. trending (linear/broken power-law) models via chi-squared/likelihood-ratio comparison, treating a null result as valid. Derive total dust mass (optically-thin isothermal, Lieman-Sifry et al. 2016 assumptions) and CO-derived gas mass (Hales et al. 2019 conversion framework), and compare against literature values (0.0083 ± 0.0015 M⊕ dust; 0.0001–0.003 M⊕ CO) as a pipeline validation check.

**Weeks 14–16 — Synthesis and writeup.** Assemble final geometries, overlaid radial profiles, the ratio-vs-radius trend/null result, and the mass cross-check table. Report results as uncertainty-bounded statements (e.g., statistical significance of any radial trend between specific radii). If the Step 0 fork triggered a reproducibility check, include the numerical side-by-side against ARKS values as the primary results table.

**Key deliverables:** dust and gas radial brightness profiles on a common au axis; geometry consistency comparison; uncertainty-bounded gas-to-dust ratio-vs-radius plot with trend/null test; dust and gas mass cross-check table against literature.

## Background Reading

- ARKS survey-overview paper and companion papers, A&A 705, A195 (20 January 2026)
- Lieman-Sifry et al. (2016)
- Hales et al. (2019)
