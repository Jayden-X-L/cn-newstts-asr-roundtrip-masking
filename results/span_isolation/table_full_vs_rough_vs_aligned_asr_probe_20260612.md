# Full vs Rough vs Aligned Span-Isolated ASR Probe

| setting | exposed | still_masked | no_output | other_transcript | note |
|---|---:|---:|---:|---:|---|
| Full-sentence ASR | 0 | 46 | 0 | 0 | MiMo confirmed-masked pool; all 46 masked in context |
| Rough 6s span-isolated ASR | 16 | 11 | 17 | 2 | Text-ratio approximate window |
| Aligned span-isolated ASR, machine | 10 | 9 | 13 | 14 | Direct string matcher before review |
| Aligned span-isolated ASR, reviewed | 19 | 11 | 13 | 3 | Strong exposed=17; partial unit-letter exposed=2 |
