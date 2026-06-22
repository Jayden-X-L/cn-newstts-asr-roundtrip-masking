# CosyVoice Raw-110 Human Review Summary (2026-06-14)

## Scope

- TTS: CosyVoice-300M-SFT, Raw input only.
- Pool: same 110 targeted high-risk rows used for the MiMo masked-error audit.
- ASR evidence: MiMo strict ASR and Whisper-small ASR transcripts are shown in the review page.
- Human label source: `ANNOTATION_EXPORT_DIR_PLACEHOLDER/cosyvoice_raw_110_human_review_labels_20260608 .json`.
- Outcome definition for `confirmed masked`: CosyVoice Raw TTS is wrong and at least one ASR route writes the expected/surface-correct form.

## Yield

### Overall outcome

| category | count | share |
|---|---:|---:|
| confirmed masked | 51 | 46.4% |
| exposed TTS error | 27 | 24.5% |
| no Raw TTS error | 30 | 27.3% |
| uncertain | 1 | 0.9% |
| not judgeable | 1 | 0.9% |

## ASR-Route Split within Confirmed Masked

| ASR masking route | Count | Share of confirmed masked |
|---|---:|---:|
| MiMo strict ASR writes expected/correct | 37 | 72.5% |
| Whisper-small ASR writes expected/correct | 36 | 70.6% |
| Both ASR routes write expected/correct | 22 | 43.1% |
| At least one ASR route writes expected/correct | 51 | 100.0% |

Pair counts within confirmed masked:

| MiMo strict ASR behavior | Whisper-small ASR behavior | Count |
|---|---|---:|
| writes expected/correct | writes expected/correct | 22 |
| exposes wrong reading | writes expected/correct | 14 |
| writes expected/correct | exposes wrong reading | 13 |
| writes expected/correct | not informative | 2 |

## By Primary Type

| primary_type | confirmed masked | exposed TTS error | no Raw TTS error | uncertain | not judgeable | total |
|---|---:|---:|---:|---:|---:|---:|
| generation_label | 0 | 0 | 5 | 0 | 0 | 5 |
| hyphen_range | 9 | 8 | 6 | 0 | 1 | 24 |
| kw_kwh | 7 | 3 | 5 | 0 | 0 | 15 |
| military_model | 7 | 1 | 1 | 0 | 0 | 9 |
| quarter | 1 | 4 | 7 | 0 | 0 | 12 |
| sports_score | 22 | 4 | 2 | 0 | 0 | 28 |
| tops_compute | 0 | 5 | 3 | 0 | 0 | 8 |
| vip88 | 0 | 0 | 1 | 0 | 0 | 1 |
| voltage | 5 | 2 | 0 | 1 | 0 | 8 |

## By CDRD Label

| cdrd_label | confirmed masked | exposed TTS error | no Raw TTS error | uncertain | not judgeable | total |
|---|---:|---:|---:|---:|---:|---:|
| cdrd_entity | 39 | 18 | 22 | 1 | 1 | 81 |
| cdrd_polyphone | 5 | 4 | 2 | 0 | 0 | 11 |
| non_cdrd | 7 | 5 | 6 | 0 | 0 | 18 |

## Consistency Notes

- Original human-review JSON is preserved unchanged.
- Final normalized table corrects one inconsistent dropdown on `PCP2_0081`: the outcome and evidence note indicate MiMo ASR wrote the expected `二百牛米`, so `mimo_asr_behavior` is normalized from `exposes wrong reading` to `writes expected/correct` with `normalization_note` populated.
- `confidence` is only filled for high-confidence positive/ambiguous rows in the exported review UI; blank confidence should not be read as low confidence for `no Raw TTS error` rows.

## Interpretation

The completed human review upgrades the second-TTS targeted run from a pending package to confirmed external validation evidence.
CosyVoice reproduces the same broad phenomenon: in the same high-risk pool, Raw-only synthesis contains listener-facing reading errors, and ASR can write at least some of those errors back to an expected or surface-correct transcript.
Because the pool is targeted and hard-case enriched, the 51/110 yield should not be interpreted as production prevalence.

## Outputs

- Raw JSON copy: `PROJECT_ROOT_PLACEHOLDER/mvp_eval/cosyvoice_targeted_20260608/human_labels_20260614/cosyvoice_raw_110_human_review_labels_raw_export_20260614.json`
- Final JSONL: `PROJECT_ROOT_PLACEHOLDER/mvp_eval/cosyvoice_targeted_20260608/human_labels_20260614/cosyvoice_raw_110_human_review_labels_final_20260614.jsonl`
- Final CSV: `PROJECT_ROOT_PLACEHOLDER/mvp_eval/cosyvoice_targeted_20260608/human_labels_20260614/cosyvoice_raw_110_human_review_labels_final_20260614.csv`
- Paper table: `PROJECT_ROOT_PLACEHOLDER/mvp_eval/cosyvoice_targeted_20260608/human_labels_20260614/table_cosyvoice_raw_110_human_review_yield_20260614.md`
