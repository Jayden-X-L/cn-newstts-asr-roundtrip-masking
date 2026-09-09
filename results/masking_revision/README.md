# Masking Revision Analyses

The clip-pair results in this directory are the **historical pre-repair** analysis.
For the current 44 effective pairs and MiMo diagnostic, see
[the corrected package](../clip_revision_20260909/) and
[its reproduction guide](../../docs/clip_revision.md).

See the [reproduction guide](../../docs/masking_analysis.md) for the public-only
entrypoint, input provenance, and optional Zenodo audio verification.

These results accompany the 2026-09-06 manuscript revision. They are not a claim
that the arXiv PDF or Zenodo v1.0.0 ZIP has been updated.

GitHub analysis release v1.0.3 adds the actual score-marker distribution,
recording-to-script counts, and an exploratory exact paired test. The six
original v1.0.2 result files remain unchanged. The full paired test definition
and limitations are recorded in `qwen_surface_paired_test.json`.

```bash
python3 scripts/derive_masking_analysis.py --output-dir /tmp/masking-analysis --check
```

Run this command from the repository root. The checked-in `audio_verification.json`
records the default inventory-only run; it does not certify WAV bytes on a reader's
machine. Use `--zenodo-zip` or `--audio-root` for actual audio-file verification.
