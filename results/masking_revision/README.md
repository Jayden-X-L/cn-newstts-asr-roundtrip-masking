# Masking Revision Analyses

See the [reproduction guide](../../docs/masking_analysis.md) for the public-only
entrypoint, input provenance, and optional Zenodo audio verification.

These results accompany the 2026-09-06 manuscript revision. They are not a claim
that the arXiv PDF or Zenodo v1.0.0 ZIP has been updated.

```bash
python3 scripts/derive_masking_analysis.py --output-dir /tmp/masking-analysis --check
```

Run this command from the repository root. The checked-in `audio_verification.json`
records the default inventory-only run; it does not certify WAV bytes on a reader's
machine. Use `--zenodo-zip` or `--audio-root` for actual audio-file verification.
