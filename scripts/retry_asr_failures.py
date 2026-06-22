"""Retry ASR for rows whose previous transcription refused / was empty.

Primary attempt with the configured ASR model; if that returns empty or a
refusal, fall back to `mimo-v2-omni`. Reuses existing TTS audio files.
"""
import base64
import json
import os
from pathlib import Path

import pandas as pd
import requests

from run_xiaomi_tts_asr_eval import call_asr, eval_spans  # noqa: E402

BASE = Path(__file__).resolve().parent
CONFIG_PATH = BASE / "xiaomi_api_config.json"
RES = BASE / "mvp_eval" / "tts_asr_eval_50_results.xlsx"

REFUSAL_PATTERNS = [
    "您发送", "不是音频文件", "无法转写", "抱歉，我无法", "我无法接收",
    "无法播放音频", "您好，这里有几点", '我无法"转写"', '我无法"听"',
    "请提供音频文件", "建议使用专业的语音转文字", "希望我根据您提供",
    "我很乐意帮忙", "直接转写音频内容", "作为一个AI", "作为文本生成模型",
    "上传音频", "没有附上音频", "没有收到音频", "并没有附带音频",
    "请上传音频文件",
]


def needs_retry(text):
    if text is None:
        return True
    s = str(text).strip()
    if not s or s.lower() == "nan":
        return True
    return any(p in s for p in REFUSAL_PATTERNS)


def call_omni(api_key, audio_path):
    url = "https://token-plan-cn.xiaomimimo.com/v1/chat/completions"
    audio = base64.b64encode(Path(audio_path).read_bytes()).decode()
    body = {
        "model": "mimo-v2-omni",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "input_audio", "input_audio": {"data": f"data:audio/wav;base64,{audio}"}},
                {"type": "text", "text": "请逐字转写这段中文音频，只输出转写文本。"},
            ],
        }],
        "temperature": 0,
        "max_completion_tokens": 2048,
    }
    resp = requests.post(
        url,
        headers={"api-key": api_key, "Content-Type": "application/json"},
        json=body,
        timeout=120,
        proxies={"http": None, "https": None},
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"] or ""


def main():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    api_key = os.environ[config.get("api_key_env", "MIMO_API_KEY")]
    df = pd.read_excel(RES)
    primary_ok = 0
    omni_ok = 0
    still_bad = []
    for idx, row in df.iterrows():
        if not needs_retry(row.get("asr_text")):
            continue
        audio_path = Path(str(row.get("audio_path") or ""))
        if not audio_path.exists():
            print(f"missing audio {row['case_id']} {row['pipeline']}: {audio_path}")
            continue
        text = ""
        try:
            text, _ = call_asr(config, audio_path)
        except Exception as exc:
            print(f"primary err {row['case_id']} {row['pipeline']}: {exc!r}")
        src = "primary"
        if needs_retry(text):
            try:
                text = call_omni(api_key, audio_path)
                src = "omni"
            except Exception as exc:
                print(f"omni err {row['case_id']} {row['pipeline']}: {exc!r}")
                still_bad.append((row["case_id"], row["pipeline"], str(exc)[:80]))
                continue
            if needs_retry(text):
                still_bad.append((row["case_id"], row["pipeline"], (text or "")[:80]))
                continue
            omni_ok += 1
        else:
            primary_ok += 1
        risk_spans = json.loads(row.get("risk_spans_json") or "[]")
        span_eval = eval_spans(text or "", risk_spans)
        correct = sum(1 for x in