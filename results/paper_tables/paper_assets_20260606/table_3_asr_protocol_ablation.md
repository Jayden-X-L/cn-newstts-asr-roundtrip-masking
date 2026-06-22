# ASR Protocol Ablation

| section | experiment | metric | sample | cdrd_label | pipeline | n | mean | delta_vs_raw | source | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| asr_protocol_ablation | MiMo TTS + default | auto_risk_span_accuracy | P1/P2 raw/structured, 1600 rows total | overall | raw | 196 | 0.4946 | 0.0000 | mvp_eval/p1p2/p1p2_asr_protocol_ablation_summary.json |  |
| asr_protocol_ablation | MiMo TTS + mimo_v2_omni_strict | auto_risk_span_accuracy | P1/P2 raw/structured, 1600 rows total | overall | raw | 196 | 0.7275 | 0.0000 | mvp_eval/p1p2/p1p2_asr_protocol_ablation_summary.json |  |
| asr_protocol_ablation | MiMo TTS + strict_prompt | auto_risk_span_accuracy | P1/P2 raw/structured, 1600 rows total | overall | raw | 196 | 0.6121 | 0.0000 | mvp_eval/p1p2/p1p2_asr_protocol_ablation_summary.json |  |
| asr_protocol_ablation | MiMo TTS + strict_prompt_negative_reading | auto_risk_span_accuracy | P1/P2 raw/structured, 1600 rows total | overall | raw | 196 | 0.6121 | 0.0000 | mvp_eval/p1p2/p1p2_asr_protocol_ablation_summary.json |  |
| asr_protocol_ablation | MiMo TTS + default | auto_risk_span_accuracy | P1/P2 raw/structured, 1600 rows total | overall | structured | 196 | 0.5276 | 0.0330 | mvp_eval/p1p2/p1p2_asr_protocol_ablation_summary.json |  |
| asr_protocol_ablation | MiMo TTS + mimo_v2_omni_strict | auto_risk_span_accuracy | P1/P2 raw/structured, 1600 rows total | overall | structured | 196 | 0.8046 | 0.0771 | mvp_eval/p1p2/p1p2_asr_protocol_ablation_summary.json |  |
| asr_protocol_ablation | MiMo TTS + strict_prompt | auto_risk_span_accuracy | P1/P2 raw/structured, 1600 rows total | overall | structured | 196 | 0.7826 | 0.1705 | mvp_eval/p1p2/p1p2_asr_protocol_ablation_summary.json |  |
| asr_protocol_ablation | MiMo TTS + strict_prompt_negative_reading | auto_risk_span_accuracy | P1/P2 raw/structured, 1600 rows total | overall | structured | 196 | 0.7826 | 0.1705 | mvp_eval/p1p2/p1p2_asr_protocol_ablation_summary.json |  |
