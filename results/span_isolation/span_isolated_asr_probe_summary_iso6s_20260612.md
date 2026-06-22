# Span-Isolated ASR Probe Summary (2026-06-12)

## Setup

- Input: 46 MiMo confirmed masked cases from the final 110-row targeted audit.
- Audio: MiMo Raw full utterances, cut into estimated risk-span clips.
- Clip window: 6.0 seconds centered by target string position in `raw_text`.
- ASR: MiMo v2.5 strict prompt.
- This is a first-pass diagnostic. Clip boundaries are approximate and should be refined with forced alignment if the result is used as a main paper claim.

## Overall

| isolated ASR outcome | count |
|---|---:|
| exposed | 9 |
| still_masked | 9 |
| mixed_masked_and_exposed | 0 |
| other_transcript | 11 |
| no_output | 17 |
| error | 0 |
| total rows written | 46 |
| completed without API error | 46 |

Definitions:

- `exposed`: isolated ASR contains a known wrong/raw reading and does not contain the expected or surface-correct form.
- `still_masked`: isolated ASR contains the expected reading or original surface span and does not contain a known wrong/raw reading.
- `mixed_masked_and_exposed`: isolated ASR contains both surface-correct and wrong-reading evidence.
- `other_transcript`: non-empty transcript without expected/surface or known wrong-reading match.
- `no_output`: empty/refusal/unusable transcript.

## By Primary Type

| primary_type | total | exposed | still_masked | mixed | other | no_output | error |
|---|---:|---:|---:|---:|---:|---:|---:|
| hyphen_range | 3 | 0 | 1 | 0 | 2 | 0 | 0 |
| kw_kwh | 10 | 2 | 4 | 0 | 1 | 3 | 0 |
| military_model | 9 | 1 | 1 | 0 | 2 | 5 | 0 |
| quarter | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| sports_score | 20 | 6 | 2 | 0 | 5 | 7 | 0 |
| tops_compute | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| vip88 | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| voltage | 1 | 0 | 0 | 0 | 1 | 0 | 0 |

## Files

- Manifest: `PROJECT_ROOT_PLACEHOLDER/mvp_eval/span_isolated_asr_probe_20260612/manifest_span_iso_6s_46.jsonl`
- Clips: `PROJECT_ROOT_PLACEHOLDER/mvp_eval/span_isolated_asr_probe_20260612/audio_span_iso_6s`
- JSONL results: `PROJECT_ROOT_PLACEHOLDER/mvp_eval/span_isolated_asr_probe_20260612/outputs/mimo_strict_span_iso_6s_results.jsonl`
- CSV results: `PROJECT_ROOT_PLACEHOLDER/mvp_eval/span_isolated_asr_probe_20260612/outputs/mimo_strict_span_iso_6s_results.csv`
