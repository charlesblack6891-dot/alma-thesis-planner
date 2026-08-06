Target: ET Cha (also cataloged as RECX 15 / ECHA J0843.3-7905), a low-mass T Tauri
star in the eta Chamaeleontis (eta Cha) young moving group, distance ~97 pc, age ~8-9
Myr. Known for an unusually compact protoplanetary disk given the association's
advanced age -- Woitke et al. 2011 (A&A, based on ALMA Band 7 project 2011.0.00133.S,
PI: Peter Woitke, publicly released 2013) characterized it as possibly one of the
smallest known protoplanetary disks (~10 AU), unusual for a disk this old. A separate
2020 direct-imaging study (the DESTINYS survey, arXiv:2007.05274) also reported a
close, low-mass companion to ET Cha.

ALMA observations (this project): two more recent ALMA projects targeting ET Cha as
part of a multi-target survey of sparse young stellar groups, both already public
(proprietary period expired):

- Project code 2017.1.01419.S (PI: Claudio Caceres; co-Is: Amelia Bayo, Alejandro
  Santamaria-Miranda, Lucas Cieza, Johan Olofsson, Matthias Schreiber, Carlos Eiroa,
  Hector Canovas), titled "Planet formation in sparse stellar groups." Band 6
  (~219-233 GHz, ~1.3 mm). Publicly released 2019-01-09 (one execution block) and
  2019-11-27 (a second). Angular resolution ranges ~0.17-0.88 arcsec across the
  archive's recorded execution blocks (exact combined-image resolution not
  determined here).
- Project code 2021.1.01205.S (PI: Claudio Caceres), titled "Unveiling the young
  stellar populations in two close benchmarking sparse young moving groups." Band 7
  (~344-357 GHz, ~0.85 mm). Publicly released 2022-11-19 and 2023-09-13 (multiple
  execution blocks). Angular resolution ranges ~0.08-0.36 arcsec across execution
  blocks.

Both of these project codes are also used, for a different target (MP Mus), in this
project's own `project_mp_mus_disk` dataset -- these are multi-target proposals
covering several stars in Caceres's sparse-stellar-group survey, not single-target
observations of ET Cha alone.

Publication status -- IMPORTANT CAVEAT, different from this project's other
"unpublished" test cases: both ET Cha datasets are already publicly released (not
proprietary -- release dates of 2019, 2022, and 2023 are all well in the past as of
2026-07-22), so there is no structural proprietary lock the way there was for the
W49A/HD138813/M87/IC443G test cases elsewhere in this batch. However, no dedicated
publication specifically analyzing ET Cha's data from these two project codes was
found during a literature search for this description -- unlike MP Mus, whose data
from these exact same two project codes WAS published (Aguayo et al. 2025, A&A 698,
A165). Ground truth here is therefore NOT structurally certain: absence of a found
paper is evidence from an incomplete search, not proof of non-publication, the way an
unexpired proprietary lock is. Treat any Stage 6 verdict on this dataset as
informative but not independently verified ground truth.

Data products: Band 6 (1.3 mm) and Band 7 (0.85 mm) dust continuum, consistent with
the survey's stated goal of characterizing disk populations in sparse young groups;
the exact delivered data products (continuum image only, vs. a fuller line dataset)
were not confirmed beyond the archive's band/frequency metadata.

Open items (not resolved, flagged rather than guessed):
- No dedicated ALMA-continuum paper was found analyzing ET Cha specifically under
  2017.1.01419.S or 2021.1.01205.S -- see the publication-status caveat above.
- Angular resolution/sensitivity varies substantially across the multiple execution
  blocks returned by the archive query; the final combined-image resolution actually
  usable for analysis was not determined here.
- Whether the full 2017.1.01419.S co-I list (Bayo, Santamaria-Miranda, Cieza,
  Olofsson, Schreiber, Eiroa, Canovas) also applies to 2021.1.01205.S was not
  independently confirmed.

Please propose a senior-thesis-scoped analysis idea using this data and tools
description. The idea should be tractable within one thesis timeframe, should not
require new instrumentation or data beyond what is described here, and should read as
plausible to a domain expert rather than merely novel or ambitious.
