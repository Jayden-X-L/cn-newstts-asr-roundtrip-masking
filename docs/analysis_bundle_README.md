# ASR Masking: Public Analysis Bundle v1.0.3

This self-contained bundle reproduces the 2026-09-06 revision analyses using
public text records, labels, and transcripts. It contains no manuscript PDF,
manuscript source, audio files, or model weights.

- Paper: https://arxiv.org/abs/2608.10606
- Repository release: https://github.com/Jayden-X-L/cn-newstts-asr-roundtrip-masking/releases/tag/v1.0.3
- Original audio archive: https://doi.org/10.5281/zenodo.21454402

From this directory, using Python 3.10+ (standard library only):

```bash
python3 scripts/derive_masking_analysis.py --output-dir /tmp/masking-analysis --check
python3 scripts/test_masking_analysis.py
```

The default checks the published audio inventory, not actual WAV bytes.
For full audio verification, add `--zenodo-zip /path/to/archive.zip` to the first
command. See [the reproduction guide](docs/masking_analysis.md) for provenance,
expected results, interpretation, and extracted-audio verification.

[`SHA256SUMS.txt`](SHA256SUMS.txt) covers every bundled file except itself.
Code: MIT. Data and annotations: CC BY 4.0. See the included license files and
the pinned prior-work snapshot's attribution.
