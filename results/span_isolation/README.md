# Historical Span-Isolation Records

This directory preserves the original 2026-06-12 clip boundaries, outputs and
reviewed summaries. The MiMo 18/46 diagnostic is the **pre-repair** result.

For the current results, use the [v1.0.4 corrected package](../clip_revision_20260909/)
and [reproduction guide](../../docs/clip_revision.md):

- Two reviewers accepted all 46 selected inputs after four boundary repairs.
- Two repaired inputs became full-recording identities and are excluded from
  effective context-reduction analysis.
- Qwen has 11 S-to-W transitions and surface recovery 19 -> 8 among 44 crops.
- MiMo has 16 exposed, 13 still masked, 12 no-output and 3 other outcomes among
  44 crops. This is a descriptive diagnostic, not a matched full/clip test.

The files in this directory are not overwritten by the corrected release.
