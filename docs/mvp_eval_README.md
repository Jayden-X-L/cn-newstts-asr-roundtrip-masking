# Xiaomi TTS/ASR MVP Eval 使用说明

## 1. 生成 50 条评测输入

```bash
python3 prepare_eval_50.py
```

输出：

- `mvp_eval/eval_50_input.xlsx`
- `mvp_eval/eval_50_input.jsonl`
- `mvp_eval/eval_50_summary.json`

当前每条 case 有两条 pipeline：

- `raw`：原始标题+摘要直接送 TTS。
- `structured`：使用 gold `spoken_text + pronunciation_dict` 送 TTS。

如果后续要加 `prompt_v3`，在 `eval_50_input.xlsx` 中新增对应 pipeline 行即可。

## 2. 配置小米 API

默认已经生成 `xiaomi_api_config.json`，配置为小米 OpenAI-compatible Chat Completions：

- TTS endpoint: `https://api.xiaomimimo.com/v1/chat/completions`
- TTS model: `mimo-v2.5-tts`
- ASR/audio understanding endpoint: `https://api.xiaomimimo.com/v1/chat/completions`
- ASR/audio understanding model: `mimo-v2.5`
- TTS voice: `白桦`
- Auth header: `api-key: $MIMO_API_KEY`

如果需要改音色或模型，编辑：

```text
xiaomi_api_config.json
```

设置 API Key：

```bash
export MIMO_API_KEY="<YOUR_MIMO_API_KEY>"
```

说明：

- 如果 TTS 返回 base64 音频，`response_audio.type` 填 `base64`。
- 如果 TTS 返回音频 URL，填 `url`。
- 如果 TTS 直接返回二进制音频，填 `binary`。
- 如果 TTS 返回 hex，填 `hex`。
- JSON 路径使用点号。当前配置中 TTS 音频为 `choices.0.message.audio.data`，ASR 文本为 `choices.0.message.content`。

## 3. 跑 TTS-ASR 回听

```bash
python3 run_xiaomi_tts_asr_eval.py
```

输出：

- `mvp_eval/audio/raw/*.wav`
- `mvp_eval/audio/structured/*.wav`
- `mvp_eval/tts_asr_eval_50_results.xlsx`

## 4. 核心指标

结果表中重点看：

- `risk_span_audio_accuracy`
- `risk_span_correct_count`
- `risk_span_total_count`
- `risk_span_eval_json`
- `error`

比较方式：

```text
raw vs structured
```

如果 structured 明显优于 raw，说明结构化 TTS 前端有效。
