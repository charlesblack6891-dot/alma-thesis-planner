# ALMA dataset: project 2017.1.00379.S

**Title:** Physical properties of dense gas in an AGN-driven outflow  
**PI:** Harada, Nanase  
**Science categories:** Galaxy evolution  
**Science keywords:** Merging and interacting galaxies, Outflows, jets, feedback  
**Data public since:** 2019-04-16 (last release 2020-07-27)  
**Scale:** 5 member OUS(s), 1 science target(s), estimated total size —  
**Archive-linked publications:** none recorded in the ALMA archive  

## Proposal abstract

Outflows in galaxies play an important role in terminating further star formation by expelling molecular gas, the ingredients of star formation. On the other hand, star formation activity was recently found in an AGN-induced outflow; it is likely caused by gas compression in the outflow. The change in physical properties due to such compression in the molecular gas in galactic outflows are still poorly known. Gas density and the dense gas fraction are especially important measures for the star formation efficiency. Those properties can be best studied in nearby galaxies using molecules with higher critical densities. Here we propose to observe multiple transition lines of HCN in NGC 3256 to study the dense molecular clouds we found in its outflow using the large-velocity gradient analysis. Observing at high resolution in one transition, we will also determine the cloud size and velocity widths. From the physical conditions of the molecular gas, we will assess the outflow's ability to form stars. This will be an important case study for understanding the molecular cloud properties in an AGN-driven outflow, which could lead to a further survey.

## Observations (one row per member OUS × target)

| Member OUS | Target | RA, Dec (deg) | Band | Frequency coverage (GHz) | Ang. res. (") | Vel. res. (km/s) | t_int (s) | Line sens. (mJy/bm @10km/s) | Cont. sens. (mJy/bm) | Mosaic | Products | Size (GB) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `uid://A001/X1273/Xb47` | ngc_3256 | 156.96346, -43.90461 | 7 | 338.8–340.8; 340.5–342.5; 350.5–352.5; 352.3–354.3 | 3.244 | 3.322 | 26127.0 | 6.634 | 0.2488 | no | cube | — |
| `uid://A001/X1273/Xb4b` | ngc_3256 | 156.96346, -43.90461 | 6 | 249.0–250.8; 250.7–252.6; 262.8–264.7; 264.6–266.4 | 0.237 | 4.424 | 11128.0 | 0.502 | 0.0171 | no | cube | — |
| `uid://A001/X1273/Xb4d` | ngc_3256 | 156.96346, -43.90461 | 6 | 249.0–250.8; 250.7–252.6; 262.8–264.7; 264.6–266.4 | 0.8 | 4.424 | 4173.0 | 0.749 | 0.0246 | no | cube | — |
| `uid://A001/X1273/Xb4f` | ngc_3256 | 156.96346, -43.90461 | 6 | 248.9–250.9; 250.7–252.7; 262.7–264.7; 264.5–266.5 | 4.352 | 4.425 | 37074.0 | 6.261 | 0.2227 | no | cube | — |
| `uid://A001/X1273/Xb55` | ngc_3256 | 156.96346, -43.90461 | 5 | 163.2–165.2; 164.5–166.5; 174.5–176.5; 176.3–178.3 | 7.01 | 3.297 | 28456.0 | 5.902 | 0.1252 | no | cube | — |

## Data access

All data are public and can be downloaded from the ALMA Science Archive (https://almascience.nrao.edu/aq/) by searching for project code `2017.1.00379.S`, or per member OUS UID listed above. Pipeline-calibrated measurement sets and QA2 image products are included in the archive download; data can be re-imaged with CASA.

## Scientific context (LLM annotation)

### Likely spectral lines in the coverage
(Redshift assumed: z ≈ 0.0093, NGC 3256's systemic recession velocity of ~2800 km/s)

- **HCN J=4–3** (rest 354.505 GHz) → observed ~351.2 GHz, in the 350.5–352.5 GHz window (Band 7). Primary target line — highest-J HCN transition in this proposal, tracing the densest gas.
- **HCN J=3–2** (rest 265.886 GHz) → observed ~263.4 GHz, in the 262.8–264.7 GHz window (Band 6). Second rung of the HCN ladder used for the LVG density diagnostic.
- **HCN J=2–1** (rest 177.261 GHz) → observed ~175.6 GHz, in the 174.5–176.5 GHz window (Band 5). Lowest-J HCN transition; anchors the excitation ladder together with J=3–2 and J=4–3.
- **HCO+ J=4–3** (rest 356.734 GHz) → observed ~353.4 GHz, in the 352.3–354.3 GHz window (Band 7). Companion dense-gas/ionization tracer co-observed with HCN(4–3).
- **HCO+ J=3–2** (rest 267.558 GHz) → observed ~265.1 GHz, in the 264.6–266.4 GHz window (Band 6).
- **HCO+ J=2–1** (rest 178.375 GHz) → observed ~176.7 GHz, in the 176.3–178.3 GHz window (Band 5).
- **CS J=7–6** (rest 342.883 GHz) → observed ~339.7 GHz, in the 338.8–340.8 GHz window (Band 7). Alternative high-critical-density tracer, useful cross-check on HCN-derived densities.
- **H¹³CN J=4–3** (rest 345.340 GHz) → observed ~342.1 GHz, in the 340.5–342.5 GHz window (Band 7). Optically thin isotopologue, valuable for constraining HCN(4–3) opacity.
- **SO 6₅–5₄** (rest 251.826 GHz) → observed ~249.5 GHz, in the 249.0–250.8 GHz window (Band 6). Shock/outflow chemistry tracer, plausible serendipitous or targeted detection given the outflow context.

### Scientific context
NGC 3256 is a late-stage luminous infrared merger hosting a well-studied multi-phase molecular outflow, and this frequency setup was purpose-built to bracket three rotational transitions of HCN (J=2–1, 3–2, 4–3) together with the corresponding HCO+ ladder, giving the critical-density leverage (~10^5–10^8 cm^-3 across these J levels) needed for large-velocity-gradient modeling of gas density and kinetic temperature in the outflowing clouds. The HCN/HCO+ line ratios at matched J constrain the ionization state and chemistry of the dense phase, distinguishing shock- or AGN-excited gas from gas simply undergoing gravitational compression, while the added CS(7–6) and H¹³CN(4–3) lines provide an opacity/optical-depth check that the optically thick HCN(4–3) line alone cannot give. SO, a well-established shock and grain-mantle-sputtering tracer, offers a complementary, chemically distinct probe of the compression fronts where the outflow is hypothesized to trigger star formation. The mix of angular resolutions across the Band 6 member OUS (from ~4″ down to ~0.24″) lets the team pair coarse, wide-area LVG diagnostics of the bulk outflow with a compact, high-resolution measurement of individual dense-cloud sizes and internal velocity dispersions, directly enabling the size–linewidth and virial-mass estimates cited in the proposal. Line and continuum sensitivities at these resolutions are adequate to detect the moderately extincted, warm dense gas typical of merger-driven outflows and to recover the underlying dust continuum for mass-budget sanity checks alongside the molecular gas analysis.

*Line list generated from general knowledge — verify against Splatalogue before imaging.*

