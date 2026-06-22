#!/usr/bin/env python3
"""Run a non-LLM ASR baseline with Whisper via transformers.

Default model is openai/whisper-small for speed. Set WHISPER_MODEL_ID to use
another checkpoint, e.g. openai/whisper-medium.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pandas as pd
import torch
from transformers import pipeline


ROOT = Path("PROJECT_ROOT_PLACEHOLDER")
INPUT = Path(os.environ.get("WHISPER_INPUT_XLSX", str(ROOT / "mvp_eval/p1p2/p1p2_tts_asr_raw_structured_results.xlsx")))
OUTPUT = Path(os.environ.get("WHISPER_OUTPUT_XLSX", str(ROOT / "mvp_eval/p1p2/p1p2_whisper_asr_results.xlsx")))
MODEL_ID = os.environ.get("WHISPER_MODEL_ID", "openai/whisper-small")
LIMIT = int(os.environ.get("WHISPER_LIMIT", "0") or "0")


def device_arg():
    if torch.cuda.is_available():
        return 0
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return -1


def main() -> None:
    print(json.dumps({"model": MODEL_ID, "device": str(device_arg()), "input": str(INPUT)}, ensure_ascii=False))
    asr = pipeline(
        "automatic-speech-recognition",
        model=MODEL_ID,
        device=device_arg(),
    )

    df = pd.read_excel(INPUT)
    df["error"] = df.get("error", "").fillna("").astype(str).replace("nan", "")
    df = df[df["error"].str.strip().eq("")].copy()
    if LIMIT:
        df = df.head(LIMIT)

    rows = []
    completed = set()
    if OUTPUT.exists() and not os.environ.get("WHISPER_RESTART"):
        old = pd.read_excel(OUTPUT)
        rows = old.to_dict("records")
        err = old.get("error", "").fillna("").astype(str).replace("nan", "").str.strip()
        completed = set(zip(old.loc[err.eq(""), "case_id"].astype(str), old.loc[err.eq(""), "pipeline"].astype(str)))

    for _, r in df.iterrows():
        key = (str(r["case_id"]), str(r["pipeline"]))
        if key in completed:
            continue
        audio_path = str(r["audio_path"])
        err = ""
        text = ""
        started = time.time()
        try:
            out = asr(
                audio_path,
                generate_kwargs={"language": "zh", "task": "transcribe"},
                return_timestamps=True,
            )
            text = out["text"]
        except Exception as exc:
            err = repr(exc)
        row = r.to_dict()
        row["asr_model"] = MODEL_ID
        row["asr_protocol"] = "whisper_non_llm"
        row["asr_text"] = text
        row["error"] = err
        row["latency_seconds"] = round(time.time() - started, 3)
        rows.append(row)
        pd.DataFrame(rows).to_excel(OUTPUT, index=False)
        print(f"[{len(rows)}/{len(df)}] {r['case_id']} {r['pipeline']} len={len(text)} err={bool(err)}")

    print(json.dumps({"rows": len(rows), "output": str(OUTPUT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
