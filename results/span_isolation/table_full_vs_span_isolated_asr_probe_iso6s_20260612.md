# Full-Sentence vs Span-Isolated ASR Probe (MiMo confirmed masked cases)

| ASR setting | input rows | exposed wrong reading | still masked / surface recovered | no usable output | other unresolved |
|---|---:|---:|---:|---:|---:|
| Full-sentence ASR, original audit | 46 | 0 | 46 | 0 | 0 |
| Span-isolated ASR, 6s approximate clips | 46 | 16 | 11 | 17 | 2 |

Notes:

- The 46 input rows are final confirmed MiMo masked-error cases from the 110-row targeted audit.
- Span clips are estimated from target-string position in `raw_text`, not forced-aligned boundaries.
- `exposed wrong reading` means isolated ASR transcribed a known wrong/raw reading such as `三十一至二十九`, `F杠二`, or letter-unit readings such as `一百零五K W`.
- `still masked / surface recovered` means isolated ASR still produced the intended reading or surface-correct form.
- This supports the span-isolation hypothesis directionally, but the high no-output rate means the current version is not yet a final evaluator.
