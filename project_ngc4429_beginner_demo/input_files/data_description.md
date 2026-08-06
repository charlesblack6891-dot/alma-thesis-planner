Target: NGC 4429, an early-type (lenticular, SB0) galaxy in the Virgo Cluster,
hosting a known circumnuclear molecular gas disk and a well-studied supermassive
black hole (SMBH) at its center. Coordinates (ICRS): RA = 12:27:26.503,
Dec = +11:06:27.58.

ALMA observations: Band 3, project code 2023.1.01214.S (PI: Kyoko Onishi),
observed 2024-01-09 with the 12-m array (51-antenna configuration). Four spectral
windows: three continuum-optimized windows (~86.4, 88.3, 98.4 GHz) combined into a
single wideband Band 3 continuum image, plus one line-focused window centered on
the redshifted HCN(1-0) line (rest frequency 88.6316 GHz), delivered as a 126-channel
spectral cube (channel width ~14.65 MHz, ~49.6 km/s).

Angular resolution / sensitivity: synthesized beam, measured directly from the
downloaded FITS headers, approx 1.63 x 1.55 arcsec (continuum, PA ~80 deg) and
approx 1.88 x 1.81 arcsec for the HCN(1-0) cube (PA ~80 deg) -- both coarser than
the archive's quoted "representative" spatial resolution of ~0.094 arcsec, which
evidently describes a different, more extended-baseline-weighted product than the
self-calibrated, pipeline-default-weighted images delivered for this member OUS and
used here. Field of view set by ALMA Band 3's primary beam (~60 arcsec).

Data products (already downloaded from the ALMA Science Archive as public,
pipeline-calibrated, science-ready FITS products -- no CASA calibration or imaging
was performed by this pipeline):
- Band 3 continuum image (primary-beam-corrected, Stokes I, self-calibrated):
  combines spectral windows 17/21/23/25.
- HCN(1-0) spectral-line cube (primary-beam-corrected, self-calibrated,
  "representative bandwidth" product): 320 x 320 spatial pixels, 126 velocity
  channels.

Science context: this project (proposal title "Circumnuclear Holes around
Supermassive Black Holes") targets NGC 4429 as one of three galaxies with a
previously known CO(2-1) hole in their circumnuclear region (a ~10-100 pc cavity
in molecular gas seen in roughly 20% of nearby galaxies, independent of current
nuclear activity). The proposal's stated goal is to observe HCN(1-0), CO(1-0), and
CO(6-5) in these galaxies to determine whether the circumnuclear hole is truly
devoid of gas (versus just CO(2-1)-faint) and to probe the physical state of gas in
the SMBH's immediate surroundings, to help distinguish AGN-feedback-driven versus
secular (SMBH-potential-driven, non-AGN) origins for the hole.

Publication status: checked via this pipeline's Stage 6 novelty check against
Semantic Scholar on 2026-07-29 -- VERDICT: NOT_PUBLISHED (no corroborating or
self-cited publication found for this specific project code/dataset).

Open items (not resolved from the archive metadata alone):
- The exact physical size and depth of NGC 4429's known CO(2-1) hole (referenced in
  the proposal abstract) was not independently re-derived here; it is taken as
  background context from the proposal text, not measured by this pipeline.
- CO(1-0) and CO(6-5), mentioned in the proposal abstract as also being requested,
  do not appear among this member OUS's delivered pipeline products (only HCN(1-0)
  and the Band 3 continuum are present) -- they may belong to a different member OUS,
  a different band/observation not yet public, or may not have been observed for
  this particular target within this project.

Please propose a senior-thesis-scoped analysis idea using this data and tools
description. The idea should be tractable within one thesis timeframe, should not
require new instrumentation or data beyond what is described here, and should read
as plausible to a domain expert rather than merely novel or ambitious.
