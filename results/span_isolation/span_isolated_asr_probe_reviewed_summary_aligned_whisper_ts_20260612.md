# Span-Isolated ASR Probe, Aligned Review (2026-06-12)

## Scope

- Pool: 46 prior MiMo `confirmed masked` cases.
- Alignment: Whisper-small word/chunk timestamps on the workstation, then aligned clips were transcribed by MiMo strict ASR.
- Control: each full sentence was masked by at least one case-specific ASR route; all isolated clips use MiMo strict ASR.

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
| exposed | 18 | 39.1% |
| still_masked | 12 | 26.1% |
| no_output | 13 | 28.3% |
| other_transcript | 3 | 6.5% |

## Exposure Strength

- Strong exposed cases: 16/46 (34.8%).
- Partial unit-letter exposed cases: 2/46 (4.3%).
- Total reviewed exposed cases including partial: 18/46 (39.1%).

## Interpretation

Aligned slicing reduces no-output cases compared with the rough 6s heuristic and surfaces more wrong-reading evidence.
The transition is consistent with a contextual contribution to masking, but the full-context masking route is case-specific whereas all isolated clips use MiMo strict ASR.
This is therefore a cross-route mechanism probe, not a protocol-matched accuracy metric; some aligned clips are also too short or acoustically ambiguous.

Recommended next step: rerun the aligned clips with a slightly wider minimum window/padding, or move to forced-choice acoustic scoring for expected vs. negative readings.

## Outputs

- Reviewed JSONL: `outputs/mimo_strict_aligned_whisper_ts_results.reviewed.jsonl`
- Reviewed CSV: `outputs/mimo_strict_aligned_whisper_ts_results.reviewed.csv`
- Aligned clips: `aligned_whisper_ts/clips/`
