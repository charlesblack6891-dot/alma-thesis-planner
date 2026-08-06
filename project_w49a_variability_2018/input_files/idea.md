**Title:** Deblending the Crowded Core: A Multi-Component Photometry Reanalysis of W49A's Confused UC/HC HII Regions Across the 1994–2015 VLA Epochs

**Description:** Rather than repeating a full-catalog variability census (which risks reproducing a source-by-source flux table De Pree et al. 2018 may already have published, since their own G2 result was necessarily derived by comparison against the rest of the field), this thesis targets a specific, bounded methods question: how much does source blending in W49A's most crowded subfield bias simple single-component flux measurements, and does a more rigorous deblending method change any source's apparent variability status?

Using the same archival, already flux-calibrated 3.6 cm 1994 and 2015 VLA images (0.8" resolution, B-configuration) described in the paper, the student will:

1. **Identify the confused subfield.** From the existing images, flag the subset of cataloged UC/HC HII sources (a well-known handful in W49A's densest core, e.g. the B/C/D/G clump) that are close enough at 0.8" resolution to show blended or overlapping emission, distinguishing them from the majority of isolated, cleanly separated sources.

2. **Reproduce baseline photometry.** For all sources, first apply the simple aperture/single-component measurement approach (the presumed method behind the paper's numbers) in a standard tool (CASA `imfit`/`imstat` or equivalent), reproducing the published G2 numbers as a validation check.

3. **Apply rigorous multi-component deblending.** For the flagged confused subfield only, fit simultaneous multi-component 2D Gaussian models (CASA `imfit` with multiple specified components, jointly fit per epoch) to separate overlapping sources, producing deblended peak/integrated flux estimates with propagated uncertainties.

4. **Quantify the bias.** Compare single-component vs. deblended flux measurements for the confused subfield in both epochs, characterizing systematic over/underestimation (e.g., does blending inflate integrated flux, suppress peak intensity, or both, and by how much relative to quoted measurement errors).

5. **Reassess variability with corrected photometry.** Recompute epoch-to-epoch significance for the deblended subfield sources using the corrected fluxes, checking whether any source's variability classification (significant vs. consistent with no change) changes once blending is properly accounted for — including whether G2 itself is affected by a neighbor.

The deliverable is a quantified methods correction — a specific, non-duplicative contribution regardless of what the paper's full tables already report — bounded entirely to the two existing archival epochs, using a named, learnable workflow (CASA multi-component `imfit`), and scoped to a manageable handful of confused sources rather than the full ~20–45 source catalog. Before finalizing scope, the student should pull the paper's actual tables in an afternoon to confirm the full single-component census is already published (motivating this pivot) and to identify which sources are flagged there as blended/confused, giving a concrete starting list for Step 1.
