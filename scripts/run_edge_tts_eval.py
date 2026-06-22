#!/usr/bin/env python3
"""Run a lightweight third-party TTS baseline with Microsoft Edge TTS.

This is not a local neural TTS baseline like CosyVoice. It is a practical
third-party TTS sanity check: synthesize the same raw/structured text with an
external Chinese TTS voice, then transcribe with the same strict MiMo ASR
protocol for comparability.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import subprocess
import time
from pathlib import Path

import pandas as pd
import requests

try:
    import edge_tts
except ImportError as exc:
    raise SystemExit("Missing dependency: pip install edge-tts") from exc


ROOT = Path("PROJECT_ROOT_PLACEHOLDER")
INPUT = Path(os.environ.get("EDGE_TTS_INPUT_XLSX", str(ROOT / "mvp_eval/p1p2/p1p2_eval_200_raw_structured.xlsx")))
OUTPUT = Path(os.environ.get("EDGE_TTS_OUTPUT_XLSX", str(ROOT / "mvp_eval/p1p2/p1p2_edge_tts_results.xlsx")))
AUDIO_DIR = Path(os.environ.get("EDGE_TTS_AUDIO_DIR", str(ROOT / "mvp_eval/p1p2/audio_edge_tts")))
VOICE = os.environ.get("EDGE_TTS_VOICE", "zh-CN-YunjianNeural")
LIMIT = int(os.environ.get("EDGE_TTS_LIMIT", "0") or "0")
URL = "https://token-plan-cn.xiaomimimo.com/v1/chat/completions"
KEY = os.environ.get("MIMO_API_KEY")
if not KEY:
    raise SystemExit("MIMO_API_KEY is not set.")

STRICT_ASR_PROMPT = (
    "请逐字按发音转写以下中文音频。严格要求：1) 听到的每个汉字必须用对应汉字写出，"
    "禁止把汉字数字转成阿拉伯数字（听到二零二五必须写二零二五，不能写2025）；"
    "2) 禁止把百分之十写成10%，必须写百分之十；3) 禁止把一百一十七比一百一十六写成117比116或117-116；"
    "4) 英文字母逐个保留为大写字母；5) 物理单位按发音写出，例如摄氏度/伏/千瓦/公里每小时；"
    "6) 禁止做任何归一化、简写、标点修复，逐字逐音照写。只输出转写文本本身。"
)


async def synth_mp3(text: str, out_mp3: Path) -> None:
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save(str(out_mp3))


def convert_to_wav(mp3: Path, wav: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(mp3), "-ar", "24000", "-ac", "1", str(wav)],
        check=True,
    )


def call_asr(audio_path: Path) -> tuple[str, dict]:
    audio_b64 = base64.b64encode(audio_path.read_bytes()).decode("utf-8")
    body = {
        "model": "mimo-v2.5",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "input_audio", "input_audio": {"data": f"data:audio/wav;base64,{audio_b64}"}},
                    {"type": "text", "text": STRICT_ASR_PROMPT},
                ],
            }
        ],
        "max_completion_tokens": 2048,
        "temperature": 0,
    }
    max_attempts = int(os.environ.get("EDGE_TTS_MAX_ATTEMPTS", "4"))
    backoff = float(os.environ.get("EDGE_TTS_BACKOFF_SECONDS", "5"))
    for attempt in range(max_attempts):
        resp = requests.post(
            URL,
            headers={"api-key": KEY, "Content-Type": "application/json"},
            json=body,
            timeout=180,
            proxies={"http": None, "https": None},
        )
        if resp.status_code in {429, 500, 502, 503, 504} and attempt < max_attempts - 1:
            retry_after = resp.headers.get("retry-after")
            wait = float(retry_after) if retry_after else backoff * (2 ** attempt)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"] or "", data
    return "", {}


def main() -> None:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(INPUT)
    if LIMIT:
        df = df.head(LIMIT)

    rows = []
    completed = set()
    if OUTPUT.exists() and not os.environ.get("EDGE_TTS_RESTART"):
        old = pd.read_excel(OUTPUT)
        rows = old.to_dict("records")
        err = old.get("error", "").fillna("").astype(str).replace("nan", "").str.strip()
        completed = set(zip(old.loc[err.eq(""), "case_id"].astype(str), old.loc[err.eq(""), "pipeline"].astype(str)))

    for _, r in df.iterrows():
        key = (str(r["case_id"]), str(r["pipeline"]))
        if key in completed:
            continue
        out_dir = AUDIO_DIR / str(r["pipeline"])
        out_dir.mkdir(parents=True, exist_ok=True)
        mp3 = out_dir / f"{r['case_id']}.mp3"
        wav = out_dir / f"{r['case_id']}.wav"
        err = ""
        asr_text = ""
        asr_resp = None
        started = time.time()
        try:
            if not wav.exists():
                asyncio.run(synth_mp3(str(r["tts_input_text"]), mp3))
                convert_to_wav(mp3, wav)
            asr_text, asr_resp = call_asr(wav)
        except Exception as exc:
            err = repr(exc)
        row = r.to_dict()
        row["tts_model"] = f"edge-tts:{VOICE}"
        row["asr_model"] = "mimo-v2.5"
        row["asr_protocol"] = "strict_prompt"
        row["audio_path"] = str(wav)
        row["asr_text"] = asr_text
        row["latency_seconds"] = round(time.time() - started, 3)
        row["error"] = err
        row["tts_response_json"] = json.dumps({"voice": VOICE, "provider": "edge-tts"}, ensure_ascii=False)
        row["asr_response_json"] = json.dumps(asr_resp, ensure_ascii=False)[:2000] if asr_resp else ""
        rows.append(row)
        pd.DataFrame(rows).to_excel(OUTPUT, index=False)
        print(f"[{len(rows)}/{len(df)}] {r['case_id']} {r['pipeline']} err={bool(err)}")
        row_sleep = float(os.environ.get("EDGE_TTS_ROW_SLEEP_SECONDS", "0") or "0")
        if row_sleep:
            time.sleep(row_sleep)

    print(json.dumps({"rows": len(rows), "voice": VOICE, "output": str(OUTPUT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
