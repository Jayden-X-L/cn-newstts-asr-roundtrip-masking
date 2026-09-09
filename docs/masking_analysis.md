# Reproduce the Masking Analyses

**Current clip results:** use the [boundary-corrected v1.0.5 analysis](clip_revision.md).
The 46-pair results below are the historical, pre-repair v1.0.3 results.
Sample selection, overlap, blind sensitivity and score-subset analyses remain applicable.

This entrypoint reproduces the 2026-09-06 conference-manuscript revision analyses
from public records. It does not rerun TTS/ASR or generate new listening labels.
The arXiv paper and Zenodo v1.0.0 archive are separate, unchanged releases.

## Run Offline

Python 3.10 or later is sufficient. No external Python packages, API keys,
model weights, sibling repositories, or private project folders are needed.
From the repository root (or the extracted analysis release bundle):

```bash
python3 scripts/derive_masking_analysis.py --output-dir /tmp/masking-analysis --check
```

`--check` compares nine regenerated result files against
[`results/masking_revision/`](../results/masking_revision/). It fails on a changed
result. The output directory must differ from the reference directory.
`--data-root /path/to/repository` selects another public data root.

## Verify Audio Bytes

The default run verifies the 200-entry archive inventory, not the WAV files.
`raw_audio_available` in the sample-flow table therefore means availability
recorded in that inventory. `audio_verification.json` explicitly reports
`inventory_only` and zero verified audio files.

For full verification, download the ZIP from
[Zenodo DOI 10.5281/zenodo.21454402](https://doi.org/10.5281/zenodo.21454402) and run:

```bash
python3 scripts/derive_masking_analysis.py \
  --output-dir /tmp/masking-audio-check --check \
  --zenodo-zip /path/to/zenodo_cn_newstts_supporting_package_v1.0.0.zip
```

This checks the original archive size and SHA-256, then reads all 200 Raw WAVs
and verifies their individual sizes and SHA-256 digests. It does not extract the
ZIP. A mismatched archive or missing/mismatched WAV stops the run.
Alternatively, pass `--audio-root /path/to/audio/mimo_v25_tts_p1p2_200/raw`
to verify an already extracted directory. Only the 200 Raw WAVs, not every audio
file in the full archive, are covered by this analysis check.

## Results and Interpretation

| Output | What is reproduced |
|---|---|
| `sample_flow_200_to_110.csv` | Frozen pool, original risk-rule matches, inclusion and exclusion by case |
| `prior_work_comparison.json` | Normalized full-text overlap against pinned CN-NewsTTS Bench v0.1 |
| `blind_label_sensitivity.csv` | Frozen labels, substitution of the 30 blind labels, and exclusion of seven disagreements |
| `variant_scope_audit_97.csv` | Per-file decisions for the restricted value-preserving score-relation check |
| `qwen_paired_transition_matrix.csv` | All nine Qwen full-recording-to-clip transition cells for 46 MiMo files |
| `masking_only_results.json` | The above counts, restricted ASR outcomes, and TTS case-ID overlap |
| `strict_score_marker_counts.csv` | Counts for all four eligible heard markers, including zeros |
| `strict_score_scope_summary.json` | 41 recordings, 24 scripts, and 17 scripts represented by both TTS systems |
| `qwen_surface_paired_test.json` | Exploratory exact McNemar test, binary endpoint, full 2-by-2 table, and interpretation |
| `input_checksums.csv` | Relative paths, byte sizes, and SHA-256 of the public analysis inputs |
| `audio_verification.json` | Whether this run checked an inventory or actual audio bytes |

The expected counts include 108 production and two synthetic selected cases;
45/6/58/1 after blind substitution; 44/4/55/0 after dropping disagreements;
and 41 restricted score files (18 MiMo, 23 CosyVoice), with 16 Qwen surface
recoveries and zero Paraformer recoveries. Excluding the other 56 files from the
restricted analysis does not label them correct. This check uses saved listening
notes; it is not a new blind listening study or a universal pronunciation rule.

All 18 retained MiMo recordings use the heard marker 至; all 23 retained
CosyVoice recordings use 减. No retained recording uses 到 or 负. These are
observed counts under the unchanged selection rule, not a revised filter.

The exploratory paired test groups W and O as non-S on the 46 selected MiMo
recordings (46 distinct scripts). With rows denoting full and columns denoting
clip outcomes in S/non-S order, the matrix is `[[7, 12], [0, 27]]`. The exact
two-sided conditional binomial probability for 12 versus zero discordant pairs
is `0.00048828125`. This test treats pairs as independent across scripts and
supports a directional association in the selected pool. It does not validate
clip boundaries, establish population prevalence, or isolate a language-model
mechanism.

The MiMo annotation roles are a primary annotator for 110 recordings, a second
reviewer for non-blind full-pool quality control, and a third reviewer for the
30-case label-blind relabel. The reported agreement compares the third
reviewer's labels only with the corresponding frozen primary labels. Source
text and expected readings remain visible in the blind task.

The primary labels are the frozen route-union audit labels, not single-recognizer
error rates. The MiMo input field is `public_audit_outcome`; the CosyVoice field
is `cosyvoice_outcome`. The blind subset does not replace the primary labels in
the main audit. Cross-TTS files are keyed by `(tts, probe_candidate_id)`; 97 files
correspond to 67 case IDs, not 97 independent text examples.

## Input Provenance

- [`derive_masking_analysis.py`](../scripts/derive_masking_analysis.py) declares all public inputs in `INPUTS`.
- [`masking_revision_rules.py`](../scripts/masking_revision_rules.py) preserves the targeted-pool builder's matching rules and priority order. Matching selects candidates; it does not assign listening labels.
- [`cn_newstts_real_500_texts.jsonl`](../metadata/candidate_pools/cn_newstts_real_500_texts.jsonl) is a text-only view of the already released production XLSX: `raw_title.rstrip("。") + "。" + raw_summary`, after trimming each field. All 500 reconstructed texts were checked against the original full-text records. The original XLSX hash is in the audio-inventory manifest.
- [`metadata/prior_work/cn_news_tts_bench_v0.1/`](../metadata/prior_work/cn_news_tts_bench_v0.1/) contains the exact public 200 dev and 800 test records, pinned by commit and SHA-256. This makes the comparison independent of changes to the prior repository's default branch. Zero normalized full-text matches does not establish absence of semantic or topical overlap.
- [`metadata/audio_inventory/`](../metadata/audio_inventory/) records the original Zenodo ZIP digest and the 200 Raw WAV digests from its checksum manifest. The published default result records inventory verification; actual WAV verification is optional and reports its own mode.

Historical 200-case Raw/Structured diagnostics remain in the archive for
traceability. They are not an experimental line in the current conference
manuscript and are not inputs to this entrypoint's sensitivity or paired analyses.

The release analysis ZIP contains public inputs, scripts, reference results,
provenance, and licenses. It contains no manuscript PDF, manuscript source,
model weights, or audio files. Access the paper through its official arXiv link.
