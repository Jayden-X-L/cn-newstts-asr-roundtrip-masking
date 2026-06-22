#!/usr/bin/env python3
"""Run ASR protocol ablation on an existing TTS result workbook.

Inputs:
- A workbook with audio_path and risk_spans_json.

Outputs:
- One row per original audio x ASR protocol.

Protocols:
- default: short transcription instruction.
- strict_prompt: no normalization, preserve spoken Chinese digits.
- strict_prompt_negative_reading: same transcript as strict_prompt, scored by
  rescore_eval.py negative-reading logic downstream.

This script only transcribes. Use rescore_eval.py with RESCORE_* env vars to
score the ablation workbook.
"""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path

import pandas as pd
import requests


ROOT = Path("PROJECT_ROOT_PLACEHOLDER")
INPUT = Path(os.environ.get("ASR_ABLATION_INPUT_XLSX", str(ROOT / "mvp_eval/p1p2/p1p2_tts_asr_raw_structured_results.xlsx")))
OUTPUT = Path(os.environ.get("ASR_ABLATION_OUTPUT_XLSX", str(ROOT / "mvp_eval/p1p2/p1p2_asr_protocol_ablation.xlsx")))
URL = "https://token-plan-cn.xiaomimimo.com/v1/chat/completions"
KEY = os.environ.get("MIMO_API_KEY")
if not KEY:
    raise SystemExit("MIMO_API_KEY is not set.")

STRICT_PROMPT = (
    "请逐字按发音转写以下中文音频。严格要求：1) 听到的每个汉字必须用对应汉字写出，"
    "禁止把汉字数字转成阿拉伯数字（听到二零二五必须写二零二五，不能写2025）；"
    "2) 禁止把百分之十写成10%，必须写百分之十；3) 禁止把一百一十七比一百一十六写成117比116或117-116；"
    "4) 英文字母逐个保留为大写字母；5) 物理单位按发音写出，例如摄氏度/伏/千瓦/公里每小时；"
    "6) 禁止做任何归一化、简写、标点修复，逐字逐音照写。只输出转写文本本身。"
)

PROTOCOLS = {
    "default": {
        "model": "mimo-v2.5",
        "prompt": "请逐字转写这段音频内容，只输出转写文本，不要解释。",
        "reuse_existing": False,
    },
    "strict_prompt": {
        "model": "mimo-v2.5",
        "prompt": STRICT_PROMPT,
        "reuse_existing": True,
    },
    "strict_prompt_negative_reading": {
        "model": "mimo-v2.5",
        "prompt": STRICT_PROMPT,
        "reuse_existing": True,
    },
    "mimo_v2_omni_strict": {
        "model": "mimo-v2-omni",
        "prompt": STRICT_PROMPT,
        "reuse_existing": False,
    },
}


def call_asr(audio_path: Path, prompt: str, model: str) -> str:
    audio_b64 = base64.b64encode(audio_path.read_bytes()).decode("utf-8")
    body = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "input_audio", "input_audio": {"data": f"data:audio/wav;base64,{audio_b64}"}},
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        "max_completion_tokens": 2048,
        "temperature": 0,
    }
    max_attempts = int(os.environ.get("ASR_ABLATION_MAX_ATTEMPTS", "4"))
    backoff = float(os.environ.get("ASR_ABLATION_BACKOFF_SECONDS", "5"))
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
        return resp.json()["choices"][0]["message"]["content"] or ""
    return ""


def main() -> None:
    src = pd.read_excel(INPUT)
    src["error"] = src.get("error", "").fillna("").astype(str).replace("nan", "")
    src = src[src["error"].str.strip().eq("")].copy()
    rows = []
    completed = set()
    if OUTPUT.exists() and not os.environ.get("ASR_ABLATION_RESTART"):
        old = pd.read_excel(OUTPUT)
        rows = old.to_dict("records")
        ok = old.get("error", "").fillna("").astype(str).replace("nan", "").str.strip().eq("")
        completed = set(zip(old.loc[ok, "case_id"].astype(str), old.loc[ok, "pipeline"].astype(str), old.loc[ok, "asr_protocol"].astype(str)))

    total = len(src) * len(PROTOCOLS)
    done_now = 0
    for _, r in src.iterrows():
        audio_path = Path(str(r["audio_path"]))
        for protocol, spec in PROTOCOLS.items():
            key = (str(r["case_id"]), str(r["pipeline"]), protocol)
            if key in completed:
                continue
            err = ""
            text = ""
            if spec.get("reuse_existing") and str(r.get("asr_text", "")).strip():
                text = str(r.get("asr_text", ""))
            else:
                for attempt in range(3):
                    try:
                        text = call_asr(audio_path, spec["prompt"], spec["model"])
                        if text.strip():
                            break
                    except Exception as exc:
                        err = repr(exc)
                        time.sleep(3)
            row = r.to_dict()
            row["asr_model"] = spec["model"]
            row["asr_protocol"] = protocol
            row["asr_text"] = text
            row["error"] = err
            rows.append(row)
            done_now += 1
            pd.DataFrame(rows).to_excel(OUTPUT, index=False)
            print(f"[{len(rows)}/{total}] {r['case_id']} {r['pipeline']} {protocol} err={bool(err)}")
            row_sleep = float(os.environ.get("ASR_ABLATION_ROW_SLEEP_SECONDS", "0") or "0")
            if row_sleep:
                time.sleep(row_sleep)
    print(json.dumps({"rows": len(rows), "new_rows": done_now, "output": str(OUTPUT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
