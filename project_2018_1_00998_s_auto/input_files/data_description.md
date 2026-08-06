# ALMA dataset: project 2018.1.00998.S

**Title:** Resolving the molecular gas reservoir in a distant interacting radio galaxy  
**PI:** Allison, James  
**Science categories:** Active galaxies  
**Science keywords:** Active Galactic Nuclei (AGN)/Quasars (QSO), Merging and interacting galaxies  
**Data public since:** 2020-10-25  
**Scale:** 1 member OUS(s), 1 science target(s), estimated total size —  
**Archive-linked publications:** none recorded in the ALMA archive  

## Proposal abstract

It is now well established that the evolution of supermassive black holes must be inextricably tied to that of their host galaxies. However, we do not yet fully understand the complex gas accretion mechanisms that drive both galactic and supermassive black hole growth. There is insufficient evidence from direct observation of the accreting gas, at epochs spanning much of the history of the Universe. We are using the Australian SKA Pathfinder and ALMA to determine the kinematics of atomic and molecular gas in radio galaxies out to z = 1. Here, we will use the longest baselines of ALMA to spatially resolve CO(2-1) absorption towards the active galactic nucleus of a distant (z = 0.44) radio galaxy, PKS1740-517, recently triggered through tidal interaction with a companion galaxy. We will determine if the CO(2-1) absorption (previously detected using ALMA) is seen against one or both source components, allowing us to establish a kinematical model for molecular gas in the host galaxy.

## Observations (one row per member OUS × target)

| Member OUS | Target | RA, Dec (deg) | Band | Frequency coverage (GHz) | Ang. res. (") | Vel. res. (km/s) | t_int (s) | Line sens. (mJy/bm @10km/s) | Cont. sens. (mJy/bm) | Mosaic | Products | Size (GB) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `uid://A001/X133d/X18e9` | PKS1740-517 | 266.10604, -51.7455 | 4 | 145.0–147.0; 147.0–149.0; 157.0–159.0; 159.0–160.9 | 0.034 | 1.841 | 1397.0 | 0.44 | 0.0119 | no | cube, image | — |

## Data access

All data are public and can be downloaded from the ALMA Science Archive (https://almascience.nrao.edu/aq/) by searching for project code `2018.1.00998.S`, or per member OUS UID listed above. Pipeline-calibrated measurement sets and QA2 image products are included in the archive download; data can be re-imaged with CASA.

## Scientific context (LLM annotation)

### Likely spectral lines in the coverage
*(assuming the quoted host redshift z = 0.44; observed = rest / 1.44)*

- **CO(2–1)**, rest 230.538 GHz → redshifted to ≈160.10 GHz, falling in the 159.0–160.9 GHz window. This is the explicit science target — the CO(2–1) absorption line against the AGN/radio-lobe continuum that the long-baseline observations are designed to spatially resolve.
- **CN N=2–1** hyperfine multiplet, rest ≈226.32–226.87 GHz → redshifted to ≈157.2–157.5 GHz, falling in the 157.0–159.0 GHz window. A plausible serendipitous detection tracing dense, UV/X-ray-irradiated gas near the AGN.
- **HC₃N J=25–24**, rest 227.419 GHz → redshifted to ≈158.0 GHz, also within the 157.0–159.0 GHz window. A secondary dense-gas tracer that could appear serendipitously alongside CN.
- **145.0–149.0 GHz windows** (rest-frame ≈208.8–214.6 GHz): no strong extragalactic molecular lines are expected here at z = 0.44 (this interval falls between the CS/CH₃OH forest below ~207 GHz and the ¹³CO/C¹⁸O(2–1)/CN complex above ~219 GHz). These spectral windows are best understood as continuum-only, likely placed to characterize the strong mm continuum (synchrotron core/lobe plus any dust) against which the CO(2–1) absorption profile is measured.

### Scientific context
This is a pencil-beam, ultra-long-baseline (0.034″ resolution) absorption-line study of cold molecular gas toward the nucleus of a merger-triggered radio galaxy at z = 0.44, where CO(2–1) is seen in absorption against the bright mm continuum from the AGN/radio lobes rather than in emission. Resolving the absorption spatially at parsec-to-tens-of-parsec scales lets the team test whether the absorbing gas covers one or both radio components, distinguishing a compact circumnuclear disk/torus geometry from more extended, merger-disturbed gas straddling a double core. The two continuum-dominated windows near 146–149 GHz provide the deep, precise continuum measurement (0.0119 mJy/bm) needed to normalize the absorption depth and separate spatial structure in the background source from structure in the foreground absorber — essential for any quantitative optical-depth or covering-factor analysis. The 157–161 GHz windows carry the CO(2–1) kinematics (1.84 km/s velocity resolution) plus possible serendipitous CN and HC₃N signal, which, if detected, would trace denser and more chemically processed gas than CO alone and help characterize the excitation environment near the AGN. Together, the combination of extreme angular resolution, fine velocity sampling, and deep continuum sensitivity supports building a spatially resolved kinematic model of gas inflow, rotation, or outflow feeding (or being disrupted around) the black hole during this tidally triggered episode — directly testing models linking galaxy interactions to AGN fueling at intermediate redshift.

*Line list generated from general knowledge — verify against Splatalogue before imaging.*
