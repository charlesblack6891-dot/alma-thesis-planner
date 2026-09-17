# ALMA dataset: project 2013.1.01332.S

**Title:** Dense Gas and Star Formation in Interacting Galaxy Pair NGC 4567/8 and Comparison to Galactic Dense Cores  
**PI:** Heiderman, Amanda  
**Science categories:** Galaxy evolution  
**Science keywords:** Giant Molecular Clouds (GMC) properties, Merging and interacting galaxies  
**Data public since:** 2016-08-26  
**Scale:** 1 member OUS(s), 1 science target(s), estimated total size —  
**Archive-linked publications:** none recorded in the ALMA archive  

## Proposal abstract

In order to determine the state and physical conditions of the dense molecular gas and its relation to the physics of star formation across infrared bright interacting galaxy pair NGC 4567/8 from the VIRUS-P Investigation of the eXtreme ENvironments of Starbursts (VIXENS) survey, we propose to use ALMA to obtain spatially resolved maps of HCN, HCO+, HNC, and CCH gas. We will compare the ALMA dense gas maps at matched spatial resolution to our resolved VIRUS-P integral field unit maps, and a full suite of multi-wavelength ancillary data (CO/HI maps, GALEX, Spitzer, Herschel, and HST). We will also compare the dense gas distribution in this interacting pair to a sample of Galactic high mass star forming dense cores in the same gas tracers. Understanding the physics of star formation and its relation to the dense gas content in a low-z merger and comparing to Galactic star forming regions is paramount to understand ALMA observations of high-z galaxies merging systems. Obtaining spatially resolved maps of multiple tracers of dense gas in nearby galaxy mergers is only now possible thanks to the combination of spatial resolution, sensitivity and UV coverage offered by ALMA in cycle 2.

## Observations (one row per member OUS × target)

| Member OUS | Target | RA, Dec (deg) | Band | Frequency coverage (GHz) | Ang. res. (") | Vel. res. (km/s) | t_int (s) | Line sens. (mJy/bm @10km/s) | Cont. sens. (mJy/bm) | Mosaic | Products | Size (GB) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `uid://A001/X144/X81` | VV_219 | 189.13902, 11.24346 | 3 | 86.3–88.2; 88.3–90.2; 98.9–100.8; 100.3–102.2 | 1.14 | 3.313 | 520.0 | 2.649 | 0.0528 | yes | cube | — |

## Data access

All data are public and can be downloaded from the ALMA Science Archive (https://almascience.nrao.edu/aq/) by searching for project code `2013.1.01332.S`, or per member OUS UID listed above. Pipeline-calibrated measurement sets and QA2 image products are included in the archive download; data can be re-imaged with CASA.

## Scientific context (LLM annotation)

### Likely spectral lines in the coverage

Assuming a systemic redshift z ≈ 0.0075 for the NGC 4567/4568 pair (Virgo Cluster, v_hel ≈ 2250–2260 km/s):

- **HCN J=1–0**, rest 88.6316 GHz → observed ≈ 87.96 GHz (falls in the 86.3–88.2 GHz window) — primary dense-gas tracer explicitly targeted by this proposal.
- **CCH (C₂H) N=1–0, J=3/2–1/2 and J=1/2–1/2 hyperfine complex**, rest ≈ 87.32–87.41 GHz → observed ≈ 86.6–86.7 GHz (86.3–88.2 GHz window) — PDR/diffuse-gas chemistry tracer, also an explicit science target.
- **HCO+ J=1–0**, rest 89.1885 GHz → observed ≈ 88.5 GHz (88.3–90.2 GHz window) — dense-gas tracer, sensitive to ionization and turbulence.
- **HNC J=1–0**, rest 90.6636 GHz → observed ≈ 89.98 GHz (88.3–90.2 GHz window) — dense-gas tracer; HCN/HNC ratio is a chemical thermometer.
- **HC3N J=11–10**, rest 100.076 GHz → observed ≈ 99.3 GHz (falls within the 98.9–100.8 GHz window) — a weaker, likely serendipitous hot-core/dense-gas tracer; not a primary target of this proposal but plausible as a faint detection if nuclear gas is warm and dense.

The two upper spectral windows (98.9–100.8, 100.3–102.2 GHz observed; rest-frame ≈ 99.6–103.0 GHz) appear to be configured mainly for continuum sensitivity (3 mm dust/free-free continuum) rather than additional strong molecular lines — no other bright extragalactic lines are expected in this rest-frequency range beyond the marginal HC3N feature noted above.

### Scientific context

HCN, HCO+, and HNC J=1–0 trace molecular gas at densities of ~10⁴–10⁵ cm⁻³, the reservoir most directly linked to star formation via the dense-gas star-formation relation, while CCH traces photon-dominated region chemistry at cloud edges exposed to UV radiation from young stars. In an interacting system like NGC 4567/4568, tidally driven gas inflows and shocks can enhance dense-gas fractions and alter chemistry (e.g., HCN/HNC excitation temperature effects, HCO+/HCN abundance ratios sensitive to ionization from shocks or AGN activity) relative to isolated disks, making this pair a key low-z laboratory for processes invoked in high-z mergers. The ~1.1″ resolution at these frequencies corresponds to ~90 pc at the Virgo distance (~17 Mpc), sufficient to resolve individual giant molecular cloud complexes and compare their dense-gas content directly against the VIRUS-P IFU star-formation-rate maps and multiwavelength (GALEX/Spitzer/Herschel/HST) ancillary data at matched scales. The quoted line and continuum sensitivities support spatially resolved measurements of dense-gas mass, line ratios, and depletion times across the merger, enabling a direct comparison of the dense-gas–SFR relation in this extragalactic environment to Galactic high-mass star-forming cores observed in the same tracers. Any detection of HC3N would additionally hint at localized warm, chemically evolved gas possibly associated with the most actively star-forming or shock-affected regions of the interaction.

*Line list generated from general knowledge — verify against Splatalogue before imaging.*
