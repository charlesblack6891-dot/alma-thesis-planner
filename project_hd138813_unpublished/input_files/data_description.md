Target: HD 138813, a young A0V debris-disk-hosting star in the Upper Scorpius
sub-association of Sco-Cen, at a distance of 130.3 pc.

Known disk properties (from prior work on this target, using different, already-public
data -- see "Prior ALMA coverage" below): a dust ring located within ~67-150 au, CO gas
extending to ~181 au (most of the gas within ~25-104 au), dust mass ~0.0083 +/- 0.0015
Mearth (Lieman-Sifry et al. 2016), and CO gas mass ~0.0001-0.003 Mearth (Hales et al.
2019).

Prior ALMA coverage (already public, a DIFFERENT project code from this dataset): HD
138813 is one of 24 debris-disk targets in ARKS (The ALMA survey to Resolve exoKuiper
belt Substructures), ALMA project code 2022.1.00338.L (PI: S. Marino; co-PIs A. M.
Hughes and L. Matra). ARKS's first results were published as a 10-paper series in A&A
705, A195 (20 January 2026), DOI 10.1051/0004-6361/202556489. ARKS achieved
per-target resolutions ranging from 0.04" to 0.85" (tailored per system) across its
sample; the exact resolution ARKS itself achieved specifically for HD 138813 is not
confirmed from the survey-overview paper alone.

This dataset: ALMA project code 2025.1.00062.S (PI: Luca Matra -- also a co-PI on the
ARKS large program above), Band 7 continuum, two execution blocks. Per the ALMA
archive, this project's data-release dates are 2027-07-01 and 2027-07-17 -- more than
a year in the future as of 2026-07-22, so this specific project's data remains
proprietary to the PI team; this is a structural (proprietary-lock) conclusion, not an
inference from an absent literature search. Achieved angular resolution ~0.099-0.104
arcsec, finer than ARKS's own resolution for many of its targets -- consistent with a
targeted, higher-resolution follow-up observation of this specific system rather than
a repeat of the original survey-resolution ARKS data.

Note for Stage 6 (novelty-check) testing -- a deliberately harder case than the
existing project_w49a_unpublished ground-truth example: this is not merely a shared
target with an unrelated author, but the SAME target with an OVERLAPPING PI (Matra is
a co-PI on both the already-published ARKS survey and this new, unreleased proposal).
The correct verdict is still NOT_PUBLISHED: the existing ARKS publication is for a
different project code's data (2022.1.00338.L) on this target, not for this specific
higher-resolution follow-up project's data (2025.1.00062.S), which has not itself been
used in any publication.

Open items (not resolved, flagged rather than guessed):
- The exact per-target angular resolution and any substructure/ring findings ARKS
  itself reported for HD 138813 specifically are not confirmed here -- deliberately
  left unverified so Stage 6's own literature search does that checking live, rather
  than being told the answer in advance.
- Continuum sensitivity (rms) and array configuration for 2025.1.00062.S were not
  available from the archive query used to source this description; only band,
  resolution, and release dates were confirmed via the ALMA TAP service.

Please propose a senior-thesis-scoped analysis idea using this data and tools
description. The idea should be tractable within one thesis timeframe, should not
require new instrumentation or data beyond what is described here, and should read as
plausible to a domain expert rather than merely novel or ambitious.
