# ASR-Roundtrip Evaluation Can Mask Context- and Convention-Dependent Reading Errors in Chinese News TTS

[中文说明](README.zh-CN.md)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21454402.svg)](https://doi.org/10.5281/zenodo.21454402)

This repository provides the data, annotations, ASR outputs, and evaluation tools supporting our study of ASR-roundtrip false negatives in Chinese news TTS.

**TL;DR.** ASR-roundtrip evaluation can return a surface-correct transcript for audio that a listener hears as wrong, when the correct spoken form depends on discourse context or domain convention (sports scores, aircraft models, technical units, membership names). In a 110-case targeted MiMo audit, **46 cases are confirmed masked, 9 are exposed, and 55 have no Raw TTS error**. Context isolation re-exposes local wrong-reading evidence in 18/46. A CosyVoice audit on the same candidates confirms 51 masked cases. On the 97 confirmed-masked files, **Qwen3-ASR-1.7B surface-recovers 40/97 while Paraformer-zh recovers only 2/97**. Use ASR roundtrip for screening, not as standalone ground truth.

**Extended preprint PDF:** [extended_preprint.pdf](https://github.com/Jayden-X-L/cn-newstts-asr-roundtrip-masking/blob/main/paper/extended_preprint.pdf)

**Zenodo archival dataset:** [10.5281/zenodo.21454402](https://doi.org/10.5281/zenodo.21454402)

## Development and Release Timeline

- **June 22, 2026:** The completed project materials were uploaded to GitHub in a private repository, creating a timestamped internal record.
- **July 16, 2026:** A corresponding Chinese patent application was formally filed, providing a formal priority record; the filing itself was not a public release.
- **July 22, 2026:** The extended preprint was submitted to arXiv and is currently pending category moderation. The submission history is expected to retain this date after announcement.
- **July 26, 2026:** The repository and supporting materials were publicly released on GitHub, establishing the first public disclosure.
- **July 27, 2026:** The archival dataset was published on Zenodo under DOI [10.5281/zenodo.21454402](https://doi.org/10.5281/zenodo.21454402) (v1.0.0, CC BY 4.0) and is indexed by OpenAIRE.

The arXiv identifier will be added after announcement.

It contains the lightweight, GitHub-friendly release package: paper snapshot, frozen case metadata, risk-span annotations, ASR prompts and settings, ASR outputs, scoring scripts, anonymized human labels, targeted-audit tables, and span-isolation summaries.

The source pool comprises 108,124 company-produced Chinese news scripts used in a production TTS workflow. This repository releases the 500 company-authorized production news scripts selected for the real-news candidate pool and 5,000 synthetic hard cases; it does not release the complete 108,124-item source export.

The open-source ASR controls are deliberately contrastive. The denominator is the 97 files previously labeled `confirmed masked` across the MiMo and CosyVoice audits, not all wrong-reading audio. Occurrence-aware review finds surface-correct recovery in 40/97 for Qwen3-ASR-1.7B, but only 2/97 for Paraformer-zh. On the 19 MiMo files surface-recovered by Qwen in full context, aligned-span transcription re-exposes a wrong or noncanonical form in 12. This shows that masking is reproducible outside MiMo yet strongly ASR- and protocol-dependent.

Large generated audio files are not stored in this GitHub package. They are archived in the [companion Zenodo dataset](https://doi.org/10.5281/zenodo.21454402).

## Contents

- `paper/`: compiled extended-preprint PDF snapshot.
- `metadata/frozen_benchmark/`: frozen 200-case benchmark metadata and Raw/Structured input matrices.
- `metadata/annotation_clarifications/`: post-freeze accepted-reading clarifications and documented result impact.
- `metadata/candidate_pools/`: 500 real-news candidate pool and 5K synthetic hard-case pool.
- `rules_and_schema/`: rules, label schema, prompt, and scoring schema snapshot.
- `labels/human_200/`: anonymized human listening labels and IAA files for the 200-case benchmark.
- `labels/targeted_audit_110/`: MiMo targeted-audit labels and summary tables for the 110-case audit.
- `results/paper_tables/paper_assets_20260608/targeted_audit_110_blind_relabel_30_agreement_summary_20260620.md`: agreement summary for the independent 30-case blind relabel.
- `labels/cosyvoice_110/`: CosyVoice Raw-only 110-case human-audit labels and summaries.
- `results/p1p2/`: automatic TTS/ASR result tables and protocol controls. The retained Edge TTS run is an auxiliary automatic comparison only; it was not subjected to a targeted human masking audit and is not part of the manuscript's core evidence chain.
- `results/span_isolation/`: span-isolation manifests, ASR outputs, reviewed summaries, and tables.
- `results/cosyvoice/`: CosyVoice TTS/ASR outputs and run summaries.
- `results/paraformer/`: publication-safe Paraformer-zh manifests, all 266 transcripts, occurrence-aware transcript audits, and result summaries.
- `results/qwen3_asr/`: publication-safe Qwen3-ASR manifests, 266 transcripts, occurrence-aware review overrides/audits, and full-to-aligned summaries.
- `manifests/`: generation and transcription manifests.
- `scripts/`: scripts used to construct benchmarks, run ASR/TTS evaluations, merge labels, and build audit tables.
- `docs/`: annotation guidelines and project evaluation notes.

## What Is Not Included Here

- Full 108,124-item company-produced news-script source export.
- API keys or provider credentials.
- Raw provider response payloads, including response identifiers and reasoning traces. Released records retain the final transcript, model and protocol identifiers, errors, and timing metadata needed for audit.
- Snapshot backups and intermediate working directories.
- Large audio bundles. These are distributed through the [Zenodo archival release](https://doi.org/10.5281/zenodo.21454402).

## Reproducibility Notes

The reported MiMo transcripts were generated with the audio-capable MiMo `mimo-v2.5` API using the included strict transcription prompt; `mimo-v2-omni` served as a fallback and protocol-ablation route. This package includes the API model identifiers, prompts, protocol settings, transcripts, and scoring scripts needed to audit the reported outputs and rerun the API-based protocols. MiMo TTS audio was generated through the MiMo-V2.5-TTS API with fixed settings. CosyVoice, Whisper, Paraformer, and Qwen outputs were generated with open-source components. Paraformer uses `paraformer-zh` v2.0.4 with FSMN-VAD v2.0.4 and no punctuation model, hotwords, or external language model. Its paired `use_itn` flag toggle changed none of 220 full-file or 46 aligned-clip transcripts, so it is not interpreted as an ITN ablation. Qwen3-ASR-1.7B uses an empty context and automatic language detection; it receives no source text or target-reading hint.

For audit-yield numbers reported in the paper, start from:

- `labels/targeted_audit_110/targeted_masked_error_audit_yield_review_results_final_20260612.csv`
- `results/paper_tables/paper_assets_20260608/targeted_audit_110_blind_relabel_30_agreement_summary_20260620.md`
- `results/paper_tables/paper_assets_20260608/targeted_audit_110_blind_relabel_30_agreement_20260620.csv`
- `metadata/annotation_clarifications/accepted_reading_clarifications_20260717.md`
- `labels/cosyvoice_110/cosyvoice_raw_110_human_review_labels_final_20260614.csv`
- `results/span_isolation/table_full_vs_rough_vs_aligned_asr_probe_20260612.md`
- `results/span_isolation/mimo_strict_aligned_46_reviewed.csv`
- `results/span_isolation/mimo_strict_rough_6s_46_reviewed.csv`
- `results/paraformer/paraformer_targeted_control_summary.md`
- `results/paraformer/paraformer_confirmed_97_transcript_audit.csv`
- `results/paraformer/paraformer_itn_toggle_summary.md`
- `results/qwen3_asr/qwen3_asr_1p7b_control_summary.md`
- `results/qwen3_asr/qwen3_confirmed_97_transcript_audit.csv`
- `results/qwen3_asr/qwen3_aligned_46_transcript_audit.csv`

## Citation

See `CITATION.cff`.

## Licenses

- Code and scripts: [MIT License](LICENSE).
- Released company-authorized production news scripts, synthetic cases, generated TTS audio in the companion archive, annotations, human labels, ASR transcripts, audit tables, and derived metadata: [CC BY 4.0](DATA_LICENSE.md).
