# Span-Isolated ASR Probe Reviewed Summary (2026-06-12)

## Setup

- Input: 46 final confirmed MiMo masked-error cases from the 110-row targeted audit.
- Audio: MiMo Raw full utterances cut into estimated 6-second risk-span clips.
- ASR: MiMo v2.5 strict prompt on each isolated clip.
- Boundary method: target-string position ratio in `raw_text`; no forced alignment yet.
- Reviewed labels preserve the raw transcript and only correct obvious matching-equivalence issues such as Chinese numerals, letter-unit readings, and hyphen/model renderings.

## Outcome Counts

| outcome | raw machine count | reviewed count |
|---|---:|---:|
| exposed | 9 | 16 |
| still_masked | 9 | 11 |
| mixed_masked_and_exposed | 0 | 0 |
| other_transcript | 11 | 2 |
| no_output | 17 | 17 |
| error | 0 | 0 |
| total | 46 | 46 |

## Main Readout

- Isolated ASR exposed the wrong reading in 16/46 cases (34.8%).
- Isolated ASR still masked or surface-recovered the target in 11/46 cases (23.9%).
- Isolated ASR produced no usable output in 17/46 cases (37.0%).
- Isolated ASR produced a non-empty but unresolved transcript in 2/46 cases (4.3%).

## By Primary Type

| primary_type | total | exposed | still_masked | mixed | other | no_output | error |
|---|---:|---:|---:|---:|---:|---:|---:|
| hyphen_range | 3 | 1 | 2 | 0 | 0 | 0 | 0 |
| kw_kwh | 10 | 3 | 4 | 0 | 0 | 3 | 0 |
| military_model | 9 | 3 | 1 | 0 | 0 | 5 | 0 |
| quarter | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| sports_score | 20 | 9 | 3 | 0 | 1 | 7 | 0 |
| tops_compute | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| vip88 | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| voltage | 1 | 0 | 0 | 0 | 1 | 0 | 0 |

## Interpretation

This first-pass result supports the hypothesis directionally: removing sentence-level context exposes a wrong reading in a non-trivial subset of cases. However, the high `no_output` and `other_transcript` rates show that naive text-ratio clipping is not stable enough to serve as the final evaluator. The next stronger version should use forced alignment or forced-choice acoustic scoring over expected vs negative readings.

## Files

- Raw JSONL: `mvp_eval/span_isolated_asr_probe_20260612/outputs/mimo_strict_span_iso_6s_results.jsonl`
- Reviewed JSONL: `mvp_eval/span_isolated_asr_probe_20260612/outputs/mimo_strict_span_iso_6s_results.reviewed.jsonl`
- Reviewed CSV: `mvp_eval/span_isolated_asr_probe_20260612/outputs/mimo_strict_span_iso_6s_results.reviewed.csv`
- Clips: `mvp_eval/span_isolated_asr_probe_20260612/audio_span_iso_6s`
