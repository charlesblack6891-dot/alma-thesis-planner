"""Real analysis of downloaded ALMA FITS products (Stage 13 support).

Everything upstream of this module works from metadata and LLM-written text
only. This module is the first thing in this repo that actually opens a
FITS file and measures something: it implements (in code, not via an LLM)
the beam-scaled aperture-photometry radial-profile analysis that this
project's own Stage 5/7 idea/methods loop proposed for the NGC 4429 HCN(1-0)
+ Band 3 continuum dataset (see project_ngc4429_smbh_hole/input_files/
idea.md and methods.md) -- moment maps, a simple position-velocity cut,
beam-scaled circular-aperture photometry with an explicit detection/
upper-limit rule, HCN luminosity/dense-gas-mass conversion, a central-
depression metric, and a continuum nuclear-aperture cross-check.

All numbers below come from the two downloaded FITS files themselves
(noise measured from line-free channels / a source-free annulus, fluxes
from real aperture sums) plus exactly two external constants, both cited
inline rather than silently assumed: the adopted distance and the
alpha_HCN dense-gas conversion factor.
"""
from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import astropy.units as u
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from astropy.coordinates import SkyCoord
from astropy.io import fits
from astropy.stats import sigma_clipped_stats
from astropy.visualization import AsinhStretch, ImageNormalize, PercentileInterval
from astropy.visualization.wcsaxes import SphericalCircle
from astropy.wcs import WCS
from spectral_cube import SpectralCube

# --- Adopted external constants (both cited, not fabricated) ------------
# Target distance and systemic velocity are NOT hardcoded here -- they are
# target-specific and must be passed in by the caller (run_analysis), which
# is expected to cite its source the same way the original NGC 4429 run did
# (e.g. "16.5 Mpc, Virgo Cluster mean, NGVS SBF catalog, Cantiello et al.
# 2018" / "1104 km/s heliocentric, NED"). Silently reusing one target's
# distance/velocity for a different target would corrupt every derived
# physical-scale and luminosity number without failing loudly.

# Dense-gas mass conversion factor, Gao & Solomon (2004), ApJS 152, 63,
# DOI 10.1086/383003 -- used purely as a fixed unit-conversion constant, as
# specified in methods.md, not fit to this target. This one genuinely is
# target-independent (a standard HCN(1-0)-to-dense-gas-mass conversion), so
# unlike distance/velocity it's safe to keep as a shared module constant.
ALPHA_HCN = 10.0  # Msun / (K km/s pc^2)

APERTURE_RADII_BEAMS = (1.0, 2.0, 3.0)
LINE_SEARCH_WINDOW_KMS = 300.0  # +/- window around systemic velocity searched for signal
SNR_DETECTION_THRESHOLD = 3.0


def _load_continuum(path: Path) -> tuple[np.ndarray, WCS, dict]:
    with fits.open(path) as hdul:
        data = np.squeeze(hdul[0].data)
        header = hdul[0].header
    wcs = WCS(header).celestial
    beam = dict(bmaj=header["BMAJ"] * 3600, bmin=header["BMIN"] * 3600, bpa=header["BPA"])
    return data, wcs, beam


def _beam_area_pix(header_or_beam: dict, pixel_scale_deg: float) -> float:
    bmaj_deg = header_or_beam["bmaj"] / 3600.0
    bmin_deg = header_or_beam["bmin"] / 3600.0
    omega_beam = (math.pi / (4 * math.log(2))) * bmaj_deg * bmin_deg
    pixel_area = pixel_scale_deg**2
    return omega_beam / pixel_area


def _sky_annulus_mask(shape, wcs: WCS, center: SkyCoord, r_in_arcsec: float, r_out_arcsec: float) -> np.ndarray:
    yy, xx = np.indices(shape)
    coords = wcs.pixel_to_world(xx, yy)
    sep = coords.separation(center).arcsec
    return (sep >= r_in_arcsec) & (sep <= r_out_arcsec)


def _sky_circle_mask(shape, wcs: WCS, center: SkyCoord, r_arcsec: float) -> np.ndarray:
    yy, xx = np.indices(shape)
    coords = wcs.pixel_to_world(xx, yy)
    return coords.separation(center).arcsec <= r_arcsec


@dataclass
class ApertureResult:
    radius_beams: float
    radius_arcsec: float
    radius_pc: float
    n_beams_in_aperture: float
    value: float
    error: float
    is_limit: bool
    snr: float
    unit: str


def _aperture_flux(
    image: np.ndarray,
    wcs: WCS,
    center: SkyCoord,
    radius_arcsec: float,
    beam_area_pix: float,
    pixel_area_arcsec2: float,
    rms_per_pix: float,
) -> tuple[float, float, float]:
    """Sum an image (in Jy/beam-like units) inside a circular sky aperture,
    convert to a total flux (dividing by the number of beams in the
    aperture), and propagate a formal Gaussian error from the per-pixel rms
    assuming beam-correlated pixels (n_beams independent samples)."""
    mask = _sky_circle_mask(image.shape, wcs, center, radius_arcsec)
    n_pix = mask.sum()
    aperture_area_arcsec2 = n_pix * pixel_area_arcsec2
    n_beams = aperture_area_arcsec2 / (
        beam_area_pix * pixel_area_arcsec2
    )
    total = np.nansum(image[mask])
    flux = total / beam_area_pix
    # Formal error: rms per beam * sqrt(number of independent beams).
    error = rms_per_pix * math.sqrt(max(n_beams, 1.0))
    return flux, error, n_beams


def analyze_continuum(
    continuum_fits: Path, center: SkyCoord, beam_scale_arcsec: float, figures_dir: Path, distance_mpc: float
):
    pc_per_arcsec = distance_mpc * 1e6 / 206265.0
    data, wcs, beam = _load_continuum(continuum_fits)
    pixel_scale_deg = abs(WCS(fits.getheader(continuum_fits)).celestial.wcs.cdelt[0])
    pixel_area_arcsec2 = (pixel_scale_deg * 3600) ** 2
    beam_area_pix = _beam_area_pix(beam, pixel_scale_deg)

    noise_mask = _sky_annulus_mask(data.shape, wcs, center, 5 * beam_scale_arcsec, 15 * beam_scale_arcsec)
    _, _, rms = sigma_clipped_stats(data[noise_mask & np.isfinite(data)], sigma=3.0)

    apertures = []
    for n_beam in APERTURE_RADII_BEAMS:
        r_arcsec = n_beam * beam_scale_arcsec
        flux, err, _ = _aperture_flux(data, wcs, center, r_arcsec, beam_area_pix, pixel_area_arcsec2, rms)
        snr = flux / err if err > 0 else 0.0
        is_limit = snr < SNR_DETECTION_THRESHOLD
        value = 3 * err if is_limit else flux
        apertures.append(
            ApertureResult(
                radius_beams=n_beam,
                radius_arcsec=r_arcsec,
                radius_pc=r_arcsec * pc_per_arcsec,
                n_beams_in_aperture=(r_arcsec**2) / (beam_scale_arcsec**2),
                value=value * 1e3,  # mJy
                error=err * 1e3,
                is_limit=is_limit,
                snr=snr,
                unit="mJy",
            )
        )

    # Display only a field of view comfortably inside the primary beam
    # (well beyond the largest 3-beam photometry aperture) -- outside that,
    # pb-correction amplifies noise steeply and would otherwise dominate
    # the plotted dynamic range.
    fov_mask = _sky_circle_mask(data.shape, wcs, center, 15 * beam_scale_arcsec)
    data_display = np.where(fov_mask, data, np.nan)

    fig = plt.figure(figsize=(5.5, 5))
    ax = fig.add_subplot(111, projection=wcs)
    peak = np.nanmax(data_display)
    norm = ImageNormalize(vmin=-5 * rms * 1e3, vmax=max(peak, 10 * rms) * 1e3)
    im = ax.imshow(data_display * 1e3, origin="lower", cmap="inferno", norm=norm)
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("mJy / beam")
    for n_beam in APERTURE_RADII_BEAMS:
        r_arcsec = n_beam * beam_scale_arcsec
        circ = SphericalCircle(
            (center.ra, center.dec), r_arcsec * u.arcsec, edgecolor="cyan", facecolor="none",
            lw=1.0, transform=ax.get_transform("world"), ls="--",
        )
        ax.add_patch(circ)
    ax.set_xlabel("R.A.")
    ax.set_ylabel("Dec.")
    ax.set_title("NGC 4429 -- ALMA Band 3 continuum")
    fig.tight_layout()
    fig_path = figures_dir / "continuum.png"
    fig.savefig(fig_path, dpi=200)
    plt.close(fig)

    return {
        "rms_mjy_beam": rms * 1e3,
        "beam_arcsec": (beam["bmaj"], beam["bmin"], beam["bpa"]),
        "apertures": [asdict(a) for a in apertures],
        "figure": str(fig_path),
    }


def analyze_hcn_cube(
    cube_fits: Path, center: SkyCoord, figures_dir: Path, distance_mpc: float, systemic_velocity_kms: float
):
    pc_per_arcsec = distance_mpc * 1e6 / 206265.0
    cube = SpectralCube.read(cube_fits)
    header = cube.header
    rest_freq_hz = header["RESTFRQ"]
    cube_vel = cube.with_spectral_unit(u.km / u.s, velocity_convention="radio", rest_value=rest_freq_hz * u.Hz)
    spectral_axis = cube_vel.spectral_axis.value
    dv = abs(spectral_axis[1] - spectral_axis[0])

    beam = cube.beam
    bmaj_arcsec = beam.major.to(u.arcsec).value
    bmin_arcsec = beam.minor.to(u.arcsec).value
    bpa_deg = beam.pa.to(u.deg).value
    beam_scale_arcsec = math.sqrt(bmaj_arcsec * bmin_arcsec)

    pixel_scale_deg = abs(cube.wcs.celestial.wcs.cdelt[0])
    pixel_area_arcsec2 = (pixel_scale_deg * 3600) ** 2
    beam_area_pix = _beam_area_pix({"bmaj": bmaj_arcsec, "bmin": bmin_arcsec, "bpa": bpa_deg}, pixel_scale_deg)

    in_window = np.abs(spectral_axis - systemic_velocity_kms) <= LINE_SEARCH_WINDOW_KMS
    line_free = ~in_window
    n_line_channels = int(in_window.sum())

    data = cube_vel.unmasked_data[:].value  # (nchan, ny, nx), Jy/beam
    noise_mask_2d = _sky_annulus_mask(data.shape[1:], cube.wcs.celestial, center, 5 * beam_scale_arcsec, 15 * beam_scale_arcsec)
    line_free_cube = data[line_free][:, noise_mask_2d]
    _, _, rms_per_chan = sigma_clipped_stats(line_free_cube[np.isfinite(line_free_cube)], sigma=3.0)

    moment0 = np.nansum(data[in_window], axis=0) * dv  # Jy/beam * km/s

    wcs2d = cube.wcs.celestial

    apertures = []
    for n_beam in APERTURE_RADII_BEAMS:
        r_arcsec = n_beam * beam_scale_arcsec
        flux, err, n_beams_ap = _aperture_flux(
            moment0, wcs2d, center, r_arcsec, beam_area_pix, pixel_area_arcsec2,
            rms_per_chan * dv * math.sqrt(n_line_channels),
        )
        snr = flux / err if err > 0 else 0.0
        is_limit = snr < SNR_DETECTION_THRESHOLD
        value_jykms = 3 * err if is_limit else flux
        nu_obs_ghz = rest_freq_hz / 1e9 / (1 + systemic_velocity_kms / 299792.458)
        l_hcn = 3.25e7 * value_jykms * nu_obs_ghz**-2 * distance_mpc**2
        mass = ALPHA_HCN * l_hcn
        apertures.append(
            {
                "radius_beams": n_beam,
                "radius_arcsec": r_arcsec,
                "radius_pc": r_arcsec * pc_per_arcsec,
                "flux_jy_kms": value_jykms,
                "flux_err_jy_kms": err,
                "is_limit": is_limit,
                "snr": snr,
                "l_hcn_K_kms_pc2": l_hcn,
                "mass_dense_gas_msun": mass,
            }
        )

    inner = apertures[0]
    outer_annulus_mask = _sky_annulus_mask(moment0.shape, wcs2d, center, apertures[0]["radius_arcsec"], apertures[-1]["radius_arcsec"])
    annulus_flux = np.nansum(moment0[outer_annulus_mask]) / beam_area_pix
    n_beams_annulus = outer_annulus_mask.sum() * pixel_area_arcsec2 / (beam_area_pix * pixel_area_arcsec2)
    annulus_err = rms_per_chan * dv * math.sqrt(n_line_channels) * math.sqrt(max(n_beams_annulus, 1.0))
    annulus_snr = annulus_flux / annulus_err if annulus_err > 0 else 0.0
    annulus_is_limit = annulus_snr < SNR_DETECTION_THRESHOLD
    annulus_value = 3 * annulus_err if annulus_is_limit else annulus_flux

    if inner["flux_jy_kms"] > 0 and annulus_value > 0:
        depression_metric = math.log10(inner["flux_jy_kms"]) - math.log10(annulus_value)
    else:
        depression_metric = None

    if inner["is_limit"] and annulus_is_limit:
        interpretation = (
            "Both the central (1-beam) aperture and the 1-3 beam annulus are non-detections "
            "at the achieved sensitivity -- the data cannot distinguish a central deficit from "
            "an overall HCN(1-0)-faint nucleus; inconclusive given the limit depth."
        )
    elif inner["is_limit"] and not annulus_is_limit:
        interpretation = (
            "The central aperture is a non-detection while the surrounding 1-3 beam annulus is "
            "detected, consistent with a beam-scale central deficit in HCN(1-0) emission."
        )
    elif not inner["is_limit"] and annulus_is_limit:
        interpretation = (
            "The central aperture is detected while the surrounding annulus is not, consistent "
            "with a compact, centrally concentrated (not depressed) HCN(1-0) source."
        )
    else:
        interpretation = (
            "Both regions are detected; the ratio above quantifies whether the profile is flat, "
            "centrally peaked, or centrally depressed."
        )

    # Moment maps (masked at the S/N-detection level for display only).
    # Primary-beam correction inflates the noise steeply away from the
    # pointing center, so the 3-sigma detection mask below is restricted to
    # a field of view comfortably inside the primary beam (well beyond the
    # largest photometry aperture, 3 beam radii) -- otherwise pb-amplified
    # noise at the image edges is misread as widespread "detected" signal.
    fov_mask_2d = _sky_circle_mask(moment0.shape, wcs2d, center, 15 * beam_scale_arcsec)
    mom1 = np.full(moment0.shape, np.nan)
    mom2 = np.full(moment0.shape, np.nan)
    signal = data[in_window]
    vel_window = spectral_axis[in_window]
    mask3d = (signal > 3 * rms_per_chan) & fov_mask_2d[None, :, :]
    weight_sum = np.nansum(np.where(mask3d, signal, 0.0), axis=0)
    with np.errstate(invalid="ignore", divide="ignore"):
        vel_grid = vel_window[:, None, None] * np.ones_like(signal)
        mom1_num = np.nansum(np.where(mask3d, signal * vel_grid, 0.0), axis=0)
        mom1 = np.where(weight_sum > 0, mom1_num / weight_sum, np.nan)
        mom2_num = np.nansum(np.where(mask3d, signal * (vel_grid - mom1) ** 2, 0.0), axis=0)
        mom2 = np.where(weight_sum > 0, np.sqrt(np.abs(mom2_num / weight_sum)), np.nan)

    n_detected_pix = int(np.sum(weight_sum > 0))
    if n_detected_pix < 5:
        kinematic_note = (
            f"Only {n_detected_pix} spatial pixels exceed the 3-sigma per-channel detection "
            "threshold anywhere in the searched velocity window -- too few to construct a "
            "meaningful velocity field or assess rotation; the moment-1/2 maps are dominated "
            "by noise and are reported for completeness only."
        )
    else:
        vmin, vmax = np.nanmin(mom1), np.nanmax(mom1)
        kinematic_note = (
            f"{n_detected_pix} spatial pixels exceed the 3-sigma per-channel threshold, spanning "
            f"a moment-1 velocity range of {vmin:.0f} to {vmax:.0f} km/s "
            f"(systemic = {systemic_velocity_kms:.0f} km/s)."
        )

    moment0_display = np.where(fov_mask_2d, moment0, np.nan)
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2), subplot_kw={"projection": wcs2d})
    for ax, img, title, cmap, unit in zip(
        axes,
        [moment0_display, mom1, mom2],
        ["Moment 0 (HCN 1-0)", "Moment 1 (velocity)", "Moment 2 (dispersion)"],
        ["viridis", "coolwarm", "magma"],
        ["Jy/beam km/s", "km/s", "km/s"],
    ):
        if title.startswith("Moment 0"):
            mom0_rms = rms_per_chan * dv * math.sqrt(n_line_channels)
            finite_vals = img[np.isfinite(img)]
            peak0 = np.nanmax(finite_vals) if finite_vals.size else mom0_rms
            norm = ImageNormalize(vmin=-3 * mom0_rms, vmax=max(peak0, 5 * mom0_rms))
            im = ax.imshow(img, origin="lower", cmap=cmap, norm=norm)
        else:
            im = ax.imshow(img, origin="lower", cmap=cmap)
        fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label=unit)
        ax.set_title(title)
        ax.set_xlabel("R.A.")
        ax.set_ylabel("Dec.")
    fig.suptitle("NGC 4429 -- HCN(1-0)")
    fig.tight_layout()
    mom_fig_path = figures_dir / "hcn_moments.png"
    fig.savefig(mom_fig_path, dpi=200)
    plt.close(fig)

    # Simple position-velocity cut along the image x-axis (R.A. direction)
    # through the nucleus row -- no disk position angle is available in the
    # archive metadata for this target, so this is a fixed, PA-agnostic
    # slice rather than a major-axis cut (documented limitation).
    ny, nx = data.shape[1], data.shape[2]
    yy, xx = np.indices((ny, nx))
    coords2d = wcs2d.pixel_to_world(xx, yy)
    sep = coords2d.separation(center).arcsec
    nucleus_row, nucleus_col = np.unravel_index(np.argmin(sep), sep.shape)
    strip_full = data[:, max(nucleus_row - 1, 0):nucleus_row + 2, :].mean(axis=1)  # (nchan, nx)
    # Zoom to +/- 2x the line-search window around systemic velocity for
    # readability; the full cube spans a much wider (mostly line-free,
    # noise-only) range that would otherwise dominate the plot.
    zoom = np.abs(spectral_axis - systemic_velocity_kms) <= 2 * LINE_SEARCH_WINDOW_KMS
    strip = strip_full[zoom]
    vel_zoom = spectral_axis[zoom]

    fig2, ax2 = plt.subplots(figsize=(6, 4.5))
    extent = [0, nx, vel_zoom[0], vel_zoom[-1]]
    im2 = ax2.imshow(strip, origin="lower", aspect="auto", extent=extent, cmap="viridis")
    ax2.axhline(systemic_velocity_kms, color="white", ls="--", lw=0.8)
    ax2.axvline(nucleus_col, color="white", ls="--", lw=0.8)
    fig2.colorbar(im2, ax=ax2, label="Jy/beam")
    ax2.set_xlabel("Pixel offset along R.A. direction")
    ax2.set_ylabel("Velocity (km/s)")
    ax2.set_title("NGC 4429 HCN(1-0) position-velocity cut (R.A. direction; no disk PA available)")
    fig2.tight_layout()
    pv_fig_path = figures_dir / "hcn_pv_diagram.png"
    fig2.savefig(pv_fig_path, dpi=200)
    plt.close(fig2)

    return {
        "rest_freq_ghz": rest_freq_hz / 1e9,
        "channel_width_kms": dv,
        "n_channels_in_line_window": n_line_channels,
        "line_search_window_kms": LINE_SEARCH_WINDOW_KMS,
        "rms_mjy_beam_per_channel": rms_per_chan * 1e3,
        "beam_arcsec": (bmaj_arcsec, bmin_arcsec, bpa_deg),
        "beam_scale_arcsec": beam_scale_arcsec,
        "apertures": apertures,
        "central_annulus_flux_jy_kms": annulus_value,
        "central_annulus_is_limit": annulus_is_limit,
        "central_depression_log_ratio": depression_metric,
        "central_depression_interpretation": interpretation,
        "kinematic_note": kinematic_note,
        "moment_figure": str(mom_fig_path),
        "pv_figure": str(pv_fig_path),
    }


def run_analysis(
    project_dir: str | Path,
    continuum_fits: Path,
    cube_fits: Path,
    ra_deg: float,
    dec_deg: float,
    target: str,
    distance_mpc: float,
    systemic_velocity_kms: float,
) -> dict:
    """Run the real HCN(1-0)+continuum analysis for `target`.

    `distance_mpc` and `systemic_velocity_kms` are target-specific and must
    be supplied by the caller with a cited source (e.g. NED) -- there is no
    safe target-independent default for either."""
    from state import figures_dir, input_files_dir

    figs = figures_dir(project_dir)
    center = SkyCoord(ra=ra_deg * u.deg, dec=dec_deg * u.deg, frame="icrs")

    hcn = analyze_hcn_cube(Path(cube_fits), center, figs, distance_mpc, systemic_velocity_kms)
    cont = analyze_continuum(Path(continuum_fits), center, hcn["beam_scale_arcsec"], figs, distance_mpc)

    results = {
        "target": target,
        "distance_mpc": distance_mpc,
        "systemic_velocity_kms": systemic_velocity_kms,
        "alpha_hcn_msun_per_K_kms_pc2": ALPHA_HCN,
        "continuum": cont,
        "hcn": hcn,
    }

    out_path = input_files_dir(project_dir) / "results.json"
    out_path.write_text(json.dumps(_to_jsonable(results), indent=2), encoding="utf-8")
    return _to_jsonable(results)


def _to_jsonable(obj):
    """Recursively convert numpy scalar/bool types to native Python types
    so every numeric field round-trips through JSON as an actual number,
    not a stringified fallback."""
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, Path):
        return str(obj)
    return obj
