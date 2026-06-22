# Human-ASR Gap Bootstrap CI

| cdrd_label | pipeline | n_cases | human_asr_gap | ci95_low | ci95_high | bootstrap_iters | notes |
|---|---|---|---|---|---|---|---|
| overall | raw | 196 | 0.2745 | 0.2184 | 0.3320 | 10000 | paired case bootstrap over aligned final auto-valid subset |
| overall | structured | 196 | 0.1667 | 0.1146 | 0.2220 | 10000 | paired case bootstrap over aligned final auto-valid subset |
| cdrd_entity | raw | 85 | 0.2190 | 0.1542 | 0.2852 | 10000 | paired case bootstrap over aligned final auto-valid subset |
| cdrd_entity | structured | 85 | 0.1564 | 0.0694 | 0.2461 | 10000 | paired case bootstrap over aligned final auto-valid subset |
| cdrd_polyphone | raw | 35 | 0.2582 | 0.1258 | 0.4036 | 10000 | paired case bootstrap over aligned final auto-valid subset |
| cdrd_polyphone | structured | 35 | 0.1644 | 0.0638 | 0.2773 | 10000 | paired case bootstrap over aligned final auto-valid subset |
| non_cdrd | raw | 76 | 0.3441 | 0.2360 | 0.4567 | 10000 | paired case bootstrap over aligned final auto-valid subset |
| non_cdrd | structured | 76 | 0.1793 | 0.0974 | 0.2690 | 10000 | paired case bootstrap over aligned final auto-valid subset |
