# Pinned Prior-Work Data

Source: Shijun Luo, CN-NewsTTS Bench,
https://github.com/Jayden-X-L/cn-news-tts-bench/tree/v0.1

`dev.jsonl` and `test_public.jsonl` are unchanged copies of `data/dev.jsonl`
and `data/test_public.jsonl` at commit
`599a4adc299140966fcbfa0412fbfb52dab19a73` (tag `v0.1`).
`manifest.json` records their SHA-256 digests. The records are CC BY 4.0;
see the parent repository's [data license](../../../DATA_LICENSE.md).

These 1,000 records are used only for normalized full-text overlap checks.
They are not additional samples in the current TTS/ASR audit.
The small numeral-rendering helper adapted in `scripts/masking_revision_rules.py`
is MIT-licensed; its original copyright and license are retained in
[`docs/licenses/cn_news_tts_bench_MIT.txt`](../../../docs/licenses/cn_news_tts_bench_MIT.txt).
