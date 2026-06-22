# Key Results Compact

| section | experiment | metric | sample | cdrd_label | pipeline | n | mean | delta_vs_raw | source | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| human_primary | P1/P2 200-case human primary, clamped | risk_span_audio_accuracy | 200 cases, raw/structured | overall | raw | 200 | 0.8889 | NA | mvp_eval/p1p2/human_labels_20260606/human_review_200_official_summary_20260606.json |  |
| human_primary | P1/P2 200-case human primary, clamped | risk_span_audio_accuracy | 200 cases, raw/structured | overall | structured | 200 | 0.9503 | 0.0614 | mvp_eval/p1p2/human_labels_20260606/human_review_200_official_summary_20260606.json |  |
| human_old_mvp | Old 3-way human review | risk_span_audio_accuracy | 20 cases, raw/prompt/structured | overall | raw | 20 | 0.8506 | 0.0000 | mvp_eval/human_review_3way_20.scored.xlsx |  |
| human_old_mvp | Old 3-way human review | risk_span_audio_accuracy | 20 cases, raw/prompt/structured | overall | prompt | 20 | 0.9825 | 0.1319 | mvp_eval/human_review_3way_20.scored.xlsx |  |
| human_old_mvp | Old 3-way human review | risk_span_audio_accuracy | 20 cases, raw/prompt/structured | overall | structured | 20 | 0.9879 | 0.1372 | mvp_eval/human_review_3way_20.scored.xlsx |  |
| human_old_mvp | Old 2-way human review | risk_span_audio_accuracy | 20 cases, raw/structured | overall | raw | 20 | 0.8204 | 0.0000 | mvp_eval/human_review_20.scored.xlsx |  |
| human_old_mvp | Old 2-way human review | risk_span_audio_accuracy | 20 cases, raw/structured | overall | structured | 20 | 0.9765 | 0.1562 | mvp_eval/human_review_20.scored.xlsx |  |
| asr_roundtrip | MiMo TTS + MiMo strict ASR | auto_risk_span_accuracy | P1/P2 200 cases x 4 pipelines; final auto-scored subset excludes human-only spans | overall | raw | 196 | 0.6121 | 0.0000 | mvp_eval/p1p2/p1p2_tts_asr_four_pipeline_summary.json |  |
| asr_roundtrip | MiMo TTS + MiMo strict ASR | auto_risk_span_accuracy | P1/P2 200 cases x 4 pipelines; final auto-scored subset excludes human-only spans | overall | prompt | 196 | 0.6605 | 0.0484 | mvp_eval/p1p2/p1p2_tts_asr_four_pipeline_summary.json |  |
| asr_roundtrip | MiMo TTS + MiMo strict ASR | auto_risk_span_accuracy | P1/P2 200 cases x 4 pipelines; final auto-scored subset excludes human-only spans | overall | polynorm | 196 | 0.6698 | 0.0577 | mvp_eval/p1p2/p1p2_tts_asr_four_pipeline_summary.json |  |
| asr_roundtrip | MiMo TTS + MiMo strict ASR | auto_risk_span_accuracy | P1/P2 200 cases x 4 pipelines; final auto-scored subset excludes human-only spans | overall | structured | 196 | 0.7826 | 0.1705 | mvp_eval/p1p2/p1p2_tts_asr_four_pipeline_summary.json |  |
| robustness_edge_tts | Edge TTS + MiMo strict ASR | auto_risk_span_accuracy | P1/P2 200 cases, raw/structured | overall | raw | 196 | 0.7219 | 0.0000 | mvp_eval/p1p2/p1p2_edge_tts_summary.json |  |
| robustness_edge_tts | Edge TTS + MiMo strict ASR | auto_risk_span_accuracy | P1/P2 200 cases, raw/structured | overall | structured | 196 | 0.8609 | 0.1390 | mvp_eval/p1p2/p1p2_edge_tts_summary.json |  |
| robustness_whisper_tiny | MiMo TTS + Whisper tiny | auto_risk_span_accuracy | P1/P2 200 cases, raw/structured | overall | raw | 196 | 0.4700 | 0.0000 | mvp_eval/p1p2/p1p2_whisper_tiny_summary.json |  |
| robustness_whisper_tiny | MiMo TTS + Whisper tiny | auto_risk_span_accuracy | P1/P2 200 cases, raw/structured | overall | structured | 196 | 0.5398 | 0.0698 | mvp_eval/p1p2/p1p2_whisper_tiny_summary.json |  |
| robustness_whisper_small | MiMo TTS + Whisper small workstation | auto_risk_span_accuracy | P1/P2 200 cases, raw/structured | overall | raw | 196 | 0.5332 | 0.0000 | mvp_eval/p1p2/p1p2_whisper_small_workstation_summary.json |  |
| robustness_whisper_small | MiMo TTS + Whisper small workstation | auto_risk_span_accuracy | P1/P2 200 cases, raw/structured | overall | structured | 196 | 0.5994 | 0.0662 | mvp_eval/p1p2/p1p2_whisper_small_workstation_summary.json |  |
| tts_prism | TTS-PRISM pronunciation evaluator | pronunciation_accuracy_0_to_5 | Old 50 cases x 4 pipelines | overall | raw | 50 | 4.5000 | 0.0000 | mvp_eval/tts_prism_results_20260530_1635/tts_prism_pipeline_summary.csv |  |
| tts_prism | TTS-PRISM pronunciation evaluator | pronunciation_accuracy_0_to_5 | Old 50 cases x 4 pipelines | overall | prompt | 50 | 4.4400 | -0.0600 | mvp_eval/tts_prism_results_20260530_1635/tts_prism_pipeline_summary.csv |  |
| tts_prism | TTS-PRISM pronunciation evaluator | pronunciation_accuracy_0_to_5 | Old 50 cases x 4 pipelines | overall | polynorm | 50 | 4.6200 | 0.1200 | mvp_eval/tts_prism_results_20260530_1635/tts_prism_pipeline_summary.csv |  |
| tts_prism | TTS-PRISM pronunciation evaluator | pronunciation_accuracy_0_to_5 | Old 50 cases x 4 pipelines | overall | structured | 50 | 4.4400 | -0.0600 | mvp_eval/tts_prism_results_20260530_1635/tts_prism_pipeline_summary.csv |  |
