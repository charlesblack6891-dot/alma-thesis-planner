# ALMA dataset: project 2017.1.00735.S

**Title:** Characterizing the Morphology, Kinematics, and Excitation in the Nuclear Region of Arp 220  
**PI:** Rangwala, Naseem  
**Science categories:** Active galaxies  
**Science keywords:** Active Galactic Nuclei (AGN)/Quasars (QSO), Merging and interacting galaxies  
**Data public since:** 2019-11-22  
**Scale:** 1 member OUS(s), 1 science target(s), estimated total size —  
**Archive-linked publications:** none recorded in the ALMA archive  

## Proposal abstract

Our ALMA observations of CO J=6-5, 3-2 and 13CO 4-3 in a late-stage galaxy merger, Arp 220, provide key insights into an important phase of galaxy evolution. Deep CO absorption (going below the continuum baseline) is detected at the centers of the merging nuclei. Evidence for a molecular outflow and a signature of an infall is found associated with the nuclear region, which also shows extreme column density and large dust optical depths. Multiple CO transitions are needed to characterize the deep absorption features seen in the two nuclei, to estimate the mass and model the excitation of the infall surrounding the nuclear disks, and to measure the spatial variation in excitation and kinematics by comparing the cold (low-J) and warm (high-J) gas maps. 12CO 4-3, 8-7, and 13CO 6-5 were part of our accepted Cy3 program but could not be observed and thus we are re-proposing them in Cy5. 13CO 6-5 will supplement 13CO 4-3 to unambiguously discriminate between absorption and outflow models and place limits on the 12C/13C isotopic ratio. Arp 220 is bright and has highly excited molecular gas and therefore makes an excellent target for utilization of ALMA at high frequencies.

## Observations (one row per member OUS × target)

| Member OUS | Target | RA, Dec (deg) | Band | Frequency coverage (GHz) | Ang. res. (") | Vel. res. (km/s) | t_int (s) | Line sens. (mJy/bm @10km/s) | Cont. sens. (mJy/bm) | Mosaic | Products | Size (GB) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `uid://A001/X1289/X1e6` | Arp_220 | 233.73843, 23.50322 | 8 | 451.9–453.8; 453.6–455.6; 463.8–465.8; 465.6–467.6 | 0.086 | 0.746 | 302.0 | 8.336 | 0.2723 | no | cube, image | — |

## Data access

All data are public and can be downloaded from the ALMA Science Archive (https://almascience.nrao.edu/aq/) by searching for project code `2017.1.00735.S`, or per member OUS UID listed above. Pipeline-calibrated measurement sets and QA2 image products are included in the archive download; data can be re-imaged with CASA.

## Scientific context (LLM annotation)

### Likely spectral lines in the coverage

- **¹²CO J=4–3** (rest 461.041 GHz) — redshifted to ≈452.8 GHz assuming Arp 220's well-known systemic redshift z = 0.018126 (cz = 5434 km/s). This falls squarely within the 451.9–453.8 and 453.6–455.6 GHz windows, and the combined ~3.7 GHz bandwidth spans ≈2450 km/s — comfortably wide enough to capture the deep nuclear absorption, blueshifted outflow wing, and redshifted infall signature described in the proposal. This is almost certainly the primary science line for this member OUS.
- **HC3N high-J transitions** (e.g., J=52–51, rest ≈473.1 GHz; J=51–50, rest ≈464.0 GHz) — tentative candidates for the 463.8–465.8 and 465.6–467.6 GHz windows, either as redshifted dense-gas tracers or near-rest-frequency serendipitous detections. Arp 220's nuclei are known hosts of luminous HC3N and vibrationally-excited HCN emission, so a real detection here is plausible but not certain from frequency coverage alone.
- **Dust continuum near 650 μm (~452–467 GHz)** — while not a spectral line, this band samples warm/hot dust continuum from the compact nuclear disks, which is the baseline against which the deep CO absorption is measured; the second pair of spectral windows may be positioned partly to secure a clean, largely line-free continuum measurement.

*No other commonly targeted extragalactic submm lines (e.g., [CI] 492/809 GHz, CO J=6–5, ¹³CO J=4–3/6–5, H2O submm lines) fall within the tabulated frequency ranges once the z = 0.018126 redshift is applied — several of these are mentioned in the proposal abstract but evidently belong to other (unlisted) member OUS/bands.*

### Scientific context

This Band 8 observation targets the CO(4–3) transition, a mid-J tracer with a critical density around 10⁴–10⁵ cm⁻³ that selectively probes warm, dense molecular gas in the compact (≲100 pc) nuclear disks of Arp 220's two merging nuclei, complementing lower-J CO data that trace the more extended, cooler gas reservoir. The extreme column densities and dust optical depths in these nuclei produce deep CO absorption against the strong submillimeter continuum, and resolving this absorption in velocity and space is what constrains models of infalling gas feeding the nuclear disks versus outflowing gas driven by nuclear activity or intense starburst feedback. The sub-0.1″ angular resolution (~30 pc at Arp 220's distance) is sufficient to spatially separate the two nuclei and resolve structure within each nuclear disk, while the broad velocity coverage captures both the systemic line and any high-velocity absorption/emission wings associated with infall or outflow. The paired continuum-adjacent windows provide the precise 650 μm continuum baseline needed to quantify absorption depth and dust optical depth, which is essential given that these nuclei are known to be optically thick well into the millimeter regime. Combined with companion CO(3–3)/¹³CO data from other observations in this program, this dataset supports excitation modeling that maps how gas temperature and density vary between the diffuse and dense nuclear components, directly addressing how gas transport and feedback operate during the terminal stage of a major gas-rich galaxy merger.

*Line list generated from general knowledge — verify against Splatalogue before imaging.*

