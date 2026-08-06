# ALMA dataset: project 2013.1.01041.S

**Title:** Revealing the progenitors of SSCs through shock dissipation in the Antennae merger  
**PI:** Herrera, Cinthya  
**Science categories:** Active galaxies  
**Science keywords:** Merging and interacting galaxies, Starbursts, star formation  
**Data public since:** 2015-11-12  
**Scale:** 1 member OUS(s), 1 science target(s), estimated total size —  
**Archive-linked publications:** none recorded in the ALMA archive  

## Proposal abstract

We identified a source we believe to be a progenitor of a massive SSC in the Antennae overlap region observing near-IR H2 emission tracing dissipation of its turbulent energy. We propose to look for other pre-cluster clouds (PCCs) with ALMA. To achieve this goal, we propose to map the overlap region in the SiO(5-4) and HNCO(10_(0,10)-9_(0,9)) line emission at an angular resolution of 0.5 arcsec, matched to the size of PCC sources. These molecules are known to be shock tracer in dense gas. The proposed ALMA observations have the combination of sensitivity and spectral and spatial resolution needed to identify several PCC sources and estimate their formation timescale.

## Observations (one row per member OUS × target)

| Member OUS | Target | RA, Dec (deg) | Band | Frequency coverage (GHz) | Ang. res. (") | Vel. res. (km/s) | t_int (s) | Line sens. (mJy/bm @10km/s) | Cont. sens. (mJy/bm) | Mosaic | Products | Size (GB) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `uid://A001/X12a/X4e` | Overlap | 180.47862, -18.88215 | 6 | 215.5–217.4; 217.8–219.7; 231.4–233.4; 233.2–235.2 | 0.268 | 1.333 | 4679.0 | 0.975 | 0.0297 | yes | cube, image | — |

## Data access

All data are public and can be downloaded from the ALMA Science Archive (https://almascience.nrao.edu/aq/) by searching for project code `2013.1.01041.S`, or per member OUS UID listed above. Pipeline-calibrated measurement sets and QA2 image products are included in the archive download; data can be re-imaged with CASA.

## Scientific context (LLM annotation)

### Likely spectral lines in the coverage

*Assumed source redshift: z ≈ 0.00537 (v_sys ≈ 1610 km/s for NGC 4038/4039, the Antennae), so observed-frame frequencies correspond to rest frequencies ≈ 1.00537× the tabulated values.*

- **SiO (v=0, J=5–4), 217.10498 GHz** — redshifts to ~216.06 GHz, inside the 215.5–217.4 GHz window. This is the proposal's primary shock/pre-cluster-cloud (PCC) tracer.
- **HNCO (10₀,₁₀–9₀,₉), 219.79827 GHz** — redshifts to ~218.62 GHz, inside the 217.8–219.7 GHz window. The second primary shock tracer targeted by the proposal.
- **C¹⁸O (J=2–1), 219.56036 GHz** — redshifts to ~218.38 GHz, falling in the same window as HNCO; likely serendipitous, tracing bulk moderately dense molecular gas.
- **¹³CO (J=2–1), 220.39868 GHz** — redshifts to ~219.22 GHz, near the upper edge of the 217.8–219.7 GHz window; serendipitous column-density/kinematic tracer.
- **H₂CO (3₀,₃–2₀,₂), 218.22219 GHz** and **CH₃OH (4₂,₂–3₁,₂ A⁺), 218.44006 GHz** — both redshift into the 215.5–217.4 GHz window (~217.1–217.3 GHz observed); grain-chemistry/shock-associated species often enhanced alongside SiO in cloud-cloud collision sites.
- **CH₃OH complex and SO₂ transitions near 233–235 GHz (rest)**, and possibly **HC₃N (J=26–25), 236.5127 GHz** at the edge of coverage — plausible but lower-confidence serendipitous lines in the two higher-frequency spectral windows (231.4–233.4, 233.2–235.2 GHz observed), which otherwise function largely as continuum windows.

### Scientific context

This dataset targets the "overlap region" of the Antennae merger, where near-IR H₂ observations previously identified candidate progenitors of super star clusters (SSCs) — pre-cluster clouds (PCCs) thought to be assembled and heated by large-scale shocks from the ongoing galaxy collision. SiO and HNCO are classic dense-gas shock tracers, released into the gas phase by grain sputtering/desorption in non-dissociative shocks, so their combined detection at 0.5″ resolution (matched to the ~10s-of-parsec scale of individual PCCs at the Antennae's distance) lets the team map where turbulent dissipation and cloud-cloud collisions are actively forming dense proto-cluster gas. The velocity resolution of ~few km/s and line sensitivity of ~1 mJy/beam at 10 km/s support measurements of individual PCC linewidths and virial masses, which combined with the SiO/HNCO line ratios can constrain shock strength and the chemical/dynamical age of each cloud — feeding directly into the proposal's goal of estimating PCC formation timescales. Serendipitous lines such as C¹⁸O, ¹³CO, H₂CO, and CH₃OH provide complementary tracers of total gas column, kinematics, and shock/ice chemistry, while the continuum sensitivity (~0.03 mJy/beam) enables dust-based mass estimates of the densest cores independent of CO-based conversions. Together, the mosaic's spatial resolution, spectral setup, and sensitivity are well matched to resolving and characterizing a population of PCCs across the overlap region rather than a single source, supporting a statistical picture of SSC progenitor formation in this canonical local merger.

*Line list generated from general knowledge — verify against Splatalogue before imaging.*
