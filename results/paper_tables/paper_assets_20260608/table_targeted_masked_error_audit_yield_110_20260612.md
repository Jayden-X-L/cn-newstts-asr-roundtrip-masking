# Targeted Masked-Error Audit Yield (110 High-Risk Candidates)

| Category | Count | Share | Meaning |
|---|---:|---:|---|
| confirmed masked | 46 | 41.8% | Raw TTS is wrong to a listener, but ASR writes an intended or surface-correct form |
| exposed TTS error | 9 | 8.2% | Raw TTS is wrong and the ASR transcript exposes or preserves the error |
| no Raw TTS error | 55 | 50.0% | Raw audio is judged correct for the audited span |
| uncertain | 0 | 0.0% | Evidence is insufficient for a final category |
| not judgeable | 0 | 0.0% | Audio, span, gold reading, or metadata is unsuitable |
| total targeted pool | 110 | 100.0% | High-risk candidates, not a production distribution |

Notes:

- The 17 earlier high-confidence masked-error cases all remain confirmed.
- The remaining 93 initially unresolved candidates are fully categorized: 29 confirmed masked, 9 exposed TTS error, and 55 no Raw TTS error.
- This is a targeted audit yield, not a production prevalence estimate.
