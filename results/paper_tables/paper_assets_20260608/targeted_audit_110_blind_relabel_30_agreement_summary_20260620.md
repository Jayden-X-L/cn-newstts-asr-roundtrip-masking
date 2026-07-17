# Targeted audit 110 blind relabel 30 agreement summary

Blind relabel source: `targeted_audit_110_blind_relabel_30_export_20260616.json` (private annotation export; anonymized agreement records are released separately).

- N: 30
- Original label counts: {'no Raw TTS error': 8, 'exposed TTS error': 7, 'confirmed masked': 15}
- Blind label counts: {'no Raw TTS error': 11, 'confirmed masked': 14, 'exposed TTS error': 4, 'uncertain': 1}
- Exact agreement, full labels including uncertain: 23/30 = 0.767
- Cohen kappa, full labels including uncertain: 0.634
- Exact agreement, three-way excluding uncertain/not judgeable rows: 23/29 = 0.793
- Cohen kappa, three-way excluding uncertain/not judgeable rows: 0.665
- Exact agreement, confirmed-masked vs other: 27/30 = 0.900; kappa = 0.800
- Exact agreement, Raw-wrong vs Raw-correct, using the blind reviewer's explicit `blind_raw_span_correctness` field: 27/30 = 0.900; kappa = 0.772

## Confusion matrix: original primary/adjudicated label x blind relabel

| original \ blind | confirmed masked | exposed TTS error | no Raw TTS error | uncertain |
|---|---:|---:|---:|---:|
| confirmed masked | 13 | 2 | 0 | 0 |
| exposed TTS error | 1 | 2 | 3 | 1 |
| no Raw TTS error | 0 | 0 | 8 | 0 |
| uncertain | 0 | 0 | 0 | 0 |

## Disagreements

- BLIND30_002 / PCP2_0086 / kw_kwh: original `exposed TTS error` -> blind `confirmed masked`. Note: Raw tts 读 500Nm 读错为：500摩尔，fallback default ASR和 MiMo omni strict ASR 都写对为 500Nm
- BLIND30_004 / PCP2_0071 / hyphen_range: original `exposed TTS error` -> blind `no Raw TTS error`. Note: 
- BLIND30_007 / PCP2_0060 / hyphen_range: original `exposed TTS error` -> blind `no Raw TTS error`. Note: 
- BLIND30_021 / PCP2_0004 / sports_score: original `confirmed masked` -> blind `exposed TTS error`. Note: 
- BLIND30_023 / PCP2_0035 / military_model: original `confirmed masked` -> blind `exposed TTS error`. Note: 
- BLIND30_024 / PCP2_0002 / sports_score: original `exposed TTS error` -> blind `uncertain`. Note: RAW读错  10后 为  十后，但是，ASR自动写为了十号。TTS、ASR都错了。
- BLIND30_025 / PCP2_0080 / kw_kwh: original `exposed TTS error` -> blind `no Raw TTS error`. Note: 
