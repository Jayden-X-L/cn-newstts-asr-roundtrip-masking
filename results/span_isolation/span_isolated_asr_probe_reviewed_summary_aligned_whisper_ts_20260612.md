# Span-Isolated ASR Probe, Aligned Review (2026-06-12)

## Scope

- Pool: 46 prior MiMo `confirmed masked` cases.
- Alignment: Whisper-small word/chunk timestamps on the workstation, then aligned clips were transcribed by MiMo strict ASR.
- Control: full-sentence MiMo strict/default ASR had masked all 46 cases by construction.

## Alignment

| alignment method | count | percent |
|---|---:|---:|
| candidate_match | 35 | 76.1% |
| nearest_chunk_fallback | 11 | 23.9% |

## Reviewed Outcome

### Full-sentence ASR baseline

| label | count | percent |
|---|---:|---:|
| exposed | 0 | 0.0% |
| still_masked | 46 | 100.0% |
| no_output | 0 | 0.0% |
| other_transcript | 0 | 0.0% |

### Rough 6s span-isolated clips

| label | count | percent |
|---|---:|---:|
| exposed | 16 | 34.8% |
| still_masked | 11 | 23.9% |
| no_output | 17 | 37.0% |
| other_transcript | 2 | 4.3% |

### Aligned span-isolated clips, machine labels

| label | count | percent |
|---|---:|---:|
| exposed | 10 | 21.7% |
| still_masked | 9 | 19.6% |
| no_output | 13 | 28.3% |
| other_transcript | 14 | 30.4% |

### Aligned span-isolated clips, reviewed labels

| label | count | percent |
|---|---:|---:|
| exposed | 19 | 41.3% |
| still_masked | 11 | 23.9% |
| no_output | 13 | 28.3% |
| other_transcript | 3 | 6.5% |

## Exposure Strength

- Strong exposed cases: 17/46 (37.0%).
- Partial unit-letter exposed cases: 2/46 (4.3%).
- Total reviewed exposed cases including partial: 19/46 (41.3%).

## Interpretation

Aligned slicing reduces no-output cases compared with the rough 6s heuristic and surfaces more masked errors.
The result supports the hypothesis that sentence context contributes to ASR masking: when the high-risk span is isolated, MiMo strict ASR often stops normalizing the reading back to the expected surface.
This remains a targeted probe rather than a main accuracy metric, because some aligned clips are still too short or acoustically ambiguous.

Recommended next step: rerun the aligned clips with a slightly wider minimum window/padding, or move to forced-choice acoustic scoring for expected vs. negative readings.

## Outputs

- Reviewed JSONL: `PROJECT_ROOT_PLACEHOLDER/mvp_eval/span_isolated_asr_probe_20260612/outputs/mimo_strict_aligned_whisper_ts_results.reviewed.jsonl`
- Reviewed CSV: `PROJECT_ROOT_PLACEHOLDER/mvp_eval/span_isolated_asr_probe_20260612/outputs/mimo_strict_aligned_whisper_ts_results.reviewed.csv`
- Aligned clips: `PROJECT_ROOT_PLACEHOLDER/mvp_eval/span_isolated_asr_probe_20260612/aligned_whisper_ts/clips`
