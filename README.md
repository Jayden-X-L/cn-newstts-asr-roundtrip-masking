# CN-NewsTTS ASR-Roundtrip Supporting Materials

This repository accompanies the preprint / conference submission:

**ASR-Roundtrip Evaluation Can Mask Context- and Convention-Dependent Reading Errors in Chinese News TTS**

It contains the lightweight, GitHub-friendly release package: paper snapshot, frozen case metadata, risk-span annotations, ASR prompts and settings, ASR outputs, scoring scripts, anonymized human labels, targeted-audit tables, and span-isolation summaries.

Large generated audio files are not stored in this GitHub package. They are prepared in the companion Zenodo package.

## Contents

- `paper/`: LaTeX source and compiled PDF snapshot.
- `metadata/frozen_benchmark/`: frozen 200-case benchmark metadata and Raw/Structured input matrices.
- `metadata/candidate_pools/`: 500 real-news candidate pool and 5K synthetic hard-case pool.
- `rules_and_schema/`: rules, label schema, prompt, and scoring schema snapshot.
- `labels/human_200/`: anonymized human listening labels and IAA files for the 200-case benchmark.
- `labels/targeted_audit_110/`: MiMo targeted-audit labels and summary tables for the 110-case audit.
- `labels/cosyvoice_110/`: CosyVoice Raw-only 110-case human-audit labels and summaries.
- `results/p1p2/`: automatic TTS/ASR result tables, ASR protocol ablation, Whisper, and Edge TTS controls.
- `results/span_isolation/`: span-isolation manifests, ASR outputs, reviewed summaries, and tables.
- `results/cosyvoice/`: CosyVoice TTS/ASR outputs and run summaries.
- `manifests/`: generation and transcription manifests.
- `scripts/`: scripts used to construct benchmarks, run ASR/TTS evaluations, merge labels, and build audit tables.
- `docs/`: annotation guidelines and project evaluation notes.

## What Is Not Included Here

- Full raw 108K news export.
- API keys or provider credentials.
- Snapshot backups and intermediate working directories.
- Large audio bundles. These are prepared for Zenodo archival release.

## Reproducibility Notes

MiMo ASR results can be reproduced with the open-source MiMo-V2.5-ASR release. MiMo TTS audio was generated through the MiMo-V2.5-TTS API with fixed settings. CosyVoice and Whisper outputs were generated with open-source components.

For audit-yield numbers reported in the paper, start from:

- `labels/targeted_audit_110/targeted_masked_error_audit_yield_review_results_final_20260612.csv`
- `labels/cosyvoice_110/cosyvoice_raw_110_human_review_labels_final_20260614.csv`
- `results/span_isolation/table_full_vs_rough_vs_aligned_asr_probe_20260612.md`

## Citation

See `CITATION.cff`.
