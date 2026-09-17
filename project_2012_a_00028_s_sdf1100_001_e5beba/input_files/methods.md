### Phase 1: Data Archive Ingestion and Image Quality Assessment

1. **Data Acquisition and Environment Setup:**
   - Ingest the pipeline-restored, science-ready FITS image products for ALMA Band 7 dataset `ADS/JAO.ALMA#2012.A.00028.S` targeting the SDF1100.001 field from the ALMA Science Archive.
   - Set up an analysis workspace using Python (with `astropy`, `spectral-cube`, and `photutils`) alongside CASA image utilities (`imhead`, `imstat`, `imview`, `imfit`).

2. **Data Product Verification:**
   - Inspect the primary-beam-corrected $1100\,\mu\text{m}$ continuum FITS image and the 3D spectral line image cube covering the line redshift range $z = 5.63 - 5.72$.
   - Confirm spatial and spectral parameters using `imhead`: spatial pixel scale, synthesized beam size (~1'' spatial resolution, corresponding to ~6 kpc assuming $z = 5.65$), image footprint ($40'' \times 40''$, spanning ~240 kpc at an assumed redshift of $z = 5.65$), and channel width across the spectral window.
   - Measure the 1$\sigma$ background noise level in emission-free regions of the $1100\,\mu\text{m}$ continuum map ($\sigma_{\text{cont}}$) and in individual channel maps of the image cube ($\sigma_{\text{channel}}$) using CASA `imstat`.

---

### Phase 2: Source Identification, Detection Verification, and 2D Spatial Mapping

1. **Validation of SMA Candidates:**
   - Query the central sky coordinates of the 7 candidate [CII]-emitting galaxies previously reported from SMA observations in the $40'' \times 40''$ region.
   - Extract localized $1100\,\mu\text{m}$ continuum fluxes and spectral profiles at these 7 SMA positions to verify line and continuum detections at the higher ALMA sensitivity level.

2. **Blind Source Searching for Faint Group Members:**
   - Conduct a systematic search for additional, fainter group members down to the ALMA sensitivity limit (approximately $10\times$ deeper than SMA in line emission and $7\times$ deeper in $1100\,\mu\text{m}$ continuum emission).
   - Search the 3D spectral cube for spatially and spectrally coherent emission line features exceeding a $3\sigma$ threshold across $\ge 2$ adjacent channels using `spectral-cube` and custom Python signal-extraction scripts.
   - Apply a automated peak-finding routine (e.g., via `photutils`) on the $1100\,\mu\text{m}$ continuum image to identify faint continuum sources down to a $3\sigma$ threshold.

3. **Moment-0 Generation and Spatial Distribution Mapping:**
   - For every verified and newly identified source, collapse spectral channels spanning the line profile to generate integrated line intensity (Moment-0) maps using CASA `immoments`.
   - Measure precise centroid positions (RA, Dec) for all detected sources by fitting 2D elliptical Gaussians to the Moment-0 and continuum images using CASA `imfit`.
   - Plot the 2D projected spatial coordinates of all group members across the $40'' \times 40''$ field of view (~240 kpc at $z = 5.65$). Quantify spatial clustering and test for structural geometry (e.g., an elongated or filamentary spatial alignment) by computing spatial pair separations and positional angles.

---

### Phase 3: 1D Spectral Extraction, Line Fitting, and Dynamic Profiling

1. **1D Spectrum Extraction:**
   - Define circular or beam-matched spatial extraction apertures centered on the 2D position of each identified source.
   - Extract 1D spectra (flux density in mJy or Jy/beam versus observed frequency) across the spectral cube using Python `spectral-cube`.

2. **Spectral Line Fitting:**
   - Fit single-component 1D Gaussian functions to the rest-frame [CII] line profiles using `scipy.optimize.curve_fit` or CASA `specfit`.
   - Derive key line parameters for each target:
     - Observed central frequency ($\nu_{\text{obs}}$) and corresponding spectroscopic redshift ($z_{[\text{CII}]}$).
     - Integrated [CII] line flux ($S_{[\text{CII}]}\Delta v$ in $\text{Jy km s}^{-1}$).
     - Line full-width at half-maximum ($\text{FWHM}_{[\text{CII}]}$ in $\text{km s}^{-1}$).

3. **Line-of-Sight Kinematics:**
   - Convert observed central frequencies into line-of-sight velocity offsets ($\Delta v_{\text{los}}$ in $\text{km s}^{-1}$) relative to an assumed group systemic redshift of $z = 5.65$ using the relativistic Doppler relation:
     $$\Delta v_{\text{los}} = c \cdot \frac{z_{[\text{CII}]} - 5.65}{1 + 5.65}$$
   - Construct a velocity distribution histogram and evaluate the dynamic velocity spread across the group members to characterize line-of-sight velocity dispersion within the structure.

---

### Phase 4: Continuum Photometry and Energetics ($L_{[\text{CII}]}/L_{\text{FIR}}$)

1. **$1100\,\mu\text{m}$ Continuum Photometry:**
   - Measure the $1100\,\mu\text{m}$ continuum flux density ($S_{1100\mu\text{m}}$) for each detected source using aperture photometry or 2D Gaussian fitting via CASA `imfit`.
   - For targets without significant continuum emission ($<3\sigma$), calculate a $3\sigma$ upper limit as $3 \times \sigma_{\text{cont}} \times \sqrt{\Omega_{\text{source}}/\Omega_{\text{beam}}}$.

2. **[CII] Line Luminosity Calculation:**
   - Calculate rest-frame [CII] line luminosities ($L_{[\text{CII}]}$ in $L_\odot$) from integrated line fluxes using the standard relation:
     $$L_{[\text{CII}]} = 1.04 \times 10^{-3} \cdot S_{[\text{CII}]}\Delta v \cdot \nu_{\text{rest}} \cdot D_L^2 \cdot (1 + z_{[\text{CII}]})^{-1}$$
     where $\nu_{\text{rest}} = 1900.536\text{ GHz}$ is the rest-frame [CII] frequency, and $D_L$ is the luminosity distance in Mpc computed for $z_{[\text{CII}]}$ assuming standard Flat $\Lambda\text{CDM}$ cosmology ($H_0 = 70\text{ km s}^{-1}\text{Mpc}^{-1}, \Omega_M = 0.3$).

3. **Far-Infrared (FIR) Luminosity Estimation:**
   - Estimate total Far-Infrared luminosity ($L_{\text{FIR}}$, integrated over rest-frame $42.5 - 500\,\mu\text{m}$) from single-band $1100\,\mu\text{m}$ continuum fluxes.
   - Adopt a standard modified blackbody (greybody) spectral energy distribution model:
     $$S_\nu \propto \nu^{\beta} B_\nu(T_{\text{dust}})$$
     under typical assumed dust parameters: dust temperature $T_{\text{dust}} \approx 40 - 50\text{ K}$ and dust emissivity index $\beta \approx 1.5 - 2.0$.
   - Integrate the modeled greybody curve over rest-frame $42.5 - 500\,\mu\text{m}$ to obtain $L_{\text{FIR}}$ for each source (or $3\sigma$ upper limits where continuum is undetected). Propagate parameter ranges ($T_{\text{dust}} = 40-50\text{ K}$, $\beta = 1.5-2.0$) into systematic uncertainties on $L_{\text{FIR}}$.

4. **$L_{[\text{CII}]}/L_{\text{FIR}}$ Energetics Analysis:**
   - Calculate the logarithmic luminosity ratio $\log_{10}(L_{[\text{CII}]}/L_{\text{FIR}})$ for every group member.
   - Compare the derived individual and group-averaged ratios against the ratio range of $10^{-2.4}$ to $10^{-2.1}$ reported from prior SMA observations to evaluate dust heating properties, radiation field intensity, and star-formation energetics in this dense environment at $z \approx 5.65$.
