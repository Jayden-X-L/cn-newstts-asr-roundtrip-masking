#!/usr/bin/env python3
"""Run Whisper ASR from a JSONL manifest.

This is intended for the workstation: it avoids pandas/openpyxl dependencies
and writes JSONL incrementally so shards can resume safely.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import torch
import soundfile as sf
from transformers import pipeline


INPUT = Path(os.environ["WHISPER_JSONL_INPUT"])
OUTPUT = Path(os.environ["WHISPER_JSONL_OUTPUT"])
MODEL_ID = os.environ.get("WHISPER_MODEL_ID", "openai/whisper-small")
LANGUAGE = os.environ.get("WHISPER_LANGUAGE", "zh")


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def completed_keys(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    done = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except Exception:
                continue
            if not str(row.get("error") or "").strip():
                done.add((str(row.get("case_id")), str(row.get("pipeline"))))
    return done


def device_arg() -> int | str:
    if torch.cuda.is_available():
        return 0
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return -1


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows = load_jsonl(INPUT)
    done = completed_keys(OUTPUT)
    device = device_arg()
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    print(json.dumps({
        "model": MODEL_ID,
        "device": str(device),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        "input_rows": len(rows),
        "already_done": len(done),
        "output": str(OUTPUT),
    }, ensure_ascii=False), flush=True)
    asr = pipeline(
        "automatic-speech-recognition",
        model=MODEL_ID,
        device=device,
        torch_dtype=dtype,
    )

    with OUTPUT.open("a", encoding="utf-8") as out_f:
        for i, row in enumerate(rows, 1):
            key = (str(row["case_id"]), str(row["pipeline"]))
            if key in done:
                continue
            err = ""
            text = ""
            started = time.time()
            try:
                audio, sampling_rate = sf.read(str(row["audio_path"]), dtype="float32")
                result = asr(
                    {"array": audio, "sampling_rate": sampling_rate},
                    generate_kwargs={"language": LANGUAGE, "task": "transcribe"},
                    return_timestamps=True,
                )
                text = result.get("text", "")
            except Exception as exc:
                err = repr(exc)
            rec = dict(row)
            rec["asr_model"] = MODEL_ID
            rec["asr_protocol"] = "whisper_non_llm"
            rec["asr_text"] = text
            rec["error"] = err
            rec["latency_seconds"] = round(time.time() - started, 3)
            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out_f.flush()
            print(f"[{i}/{len(rows)}] {row['case_id']} {row['pipeline']} len={len(text)} err={bool(err)}", flush=True)


if __name__ == "__main__":
    main()
