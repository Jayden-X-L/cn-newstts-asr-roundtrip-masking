#!/usr/bin/env python3
"""Run CosyVoice TTS from a JSONL manifest with resumable JSONL output.

This script is intended for the workstation. It does not contain credentials.
It expects a CosyVoice checkout and pretrained model directory to exist.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import torch
import torchaudio


INPUT = Path(os.environ["COSYVOICE_JSONL_INPUT"])
OUTPUT = Path(os.environ["COSYVOICE_JSONL_OUTPUT"])
AUDIO_DIR = Path(os.environ["COSYVOICE_AUDIO_DIR"])
REPO_DIR = Path(os.environ.get("COSYVOICE_REPO_DIR", "/data/ai/workspace/cn_newstts/CosyVoice"))
MODEL_DIR = Path(os.environ.get("COSYVOICE_MODEL_DIR", str(REPO_DIR / "pretrained_models/CosyVoice-300M-SFT")))
MODE = os.environ.get("COSYVOICE_MODE", "sft")
SPEAKER = os.environ.get("COSYVOICE_SPEAKER", "中文女")
LIMIT = int(os.environ.get("COSYVOICE_LIMIT", "0") or "0")
PAUSE_SECONDS = float(os.environ.get("COSYVOICE_CHUNK_PAUSE_SECONDS", "0.18"))


sys.path.insert(0, str(REPO_DIR))
sys.path.append(str(REPO_DIR / "third_party/Matcha-TTS"))

from cosyvoice.cli.cosyvoice import AutoModel  # noqa: E402


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows[:LIMIT] if LIMIT else rows


def completed_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    done: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except Exception:
                continue
            if not str(row.get("error") or "").strip() and row.get("probe_candidate_id"):
                done.add(str(row["probe_candidate_id"]))
    return done


def concat_chunks(chunks: list[torch.Tensor], sample_rate: int) -> torch.Tensor:
    if not chunks:
        raise RuntimeError("CosyVoice returned no audio chunks")
    cleaned = []
    for chunk in chunks:
        chunk = chunk.detach().cpu()
        if chunk.ndim == 1:
            chunk = chunk.unsqueeze(0)
        cleaned.append(chunk)
    if len(cleaned) == 1 or PAUSE_SECONDS <= 0:
        return torch.cat(cleaned, dim=-1)
    pause = torch.zeros(cleaned[0].shape[0], int(sample_rate * PAUSE_SECONDS))
    interleaved: list[torch.Tensor] = []
    for idx, chunk in enumerate(cleaned):
        if idx:
            interleaved.append(pause)
        interleaved.append(chunk)
    return torch.cat(interleaved, dim=-1)


def synth_one(model: AutoModel, text: str) -> tuple[torch.Tensor, int, int]:
    chunks: list[torch.Tensor] = []
    if MODE == "sft":
        iterator = model.inference_sft(text, SPEAKER, stream=False)
    else:
        raise ValueError(f"Unsupported COSYVOICE_MODE={MODE!r}")
    for item in iterator:
        chunks.append(item["tts_speech"])
    audio = concat_chunks(chunks, model.sample_rate)
    return audio, int(model.sample_rate), len(chunks)


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_jsonl(INPUT)
    done = completed_ids(OUTPUT)
    print(json.dumps({
        "input": str(INPUT),
        "output": str(OUTPUT),
        "audio_dir": str(AUDIO_DIR),
        "repo_dir": str(REPO_DIR),
        "model_dir": str(MODEL_DIR),
        "mode": MODE,
        "speaker": SPEAKER,
        "rows": len(rows),
        "already_done": len(done),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", ""),
    }, ensure_ascii=False), flush=True)

    model = AutoModel(model_dir=str(MODEL_DIR))
    print(json.dumps({
        "sample_rate": getattr(model, "sample_rate", None),
        "available_speakers": model.list_available_spks() if hasattr(model, "list_available_spks") else None,
    }, ensure_ascii=False), flush=True)

    with OUTPUT.open("a", encoding="utf-8") as out_f:
        for i, row in enumerate(rows, 1):
            pid = str(row["probe_candidate_id"])
            if pid in done:
                continue
            started = time.time()
            err = ""
            audio_path = AUDIO_DIR / f"{pid}_{row['case_id']}_raw.wav"
            sample_rate = ""
            chunk_count = 0
            duration_seconds = ""
            try:
                if not audio_path.exists():
                    audio, sample_rate, chunk_count = synth_one(model, str(row["tts_input_text"]))
                    torchaudio.save(str(audio_path), audio, sample_rate)
                    duration_seconds = round(audio.shape[-1] / sample_rate, 3)
                else:
                    info = torchaudio.info(str(audio_path))
                    sample_rate = int(info.sample_rate)
                    duration_seconds = round(info.num_frames / info.sample_rate, 3)
            except Exception as exc:
                err = repr(exc)

            rec = dict(row)
            rec.update({
                "tts_model": "CosyVoice-300M-SFT",
                "tts_system": "CosyVoice",
                "tts_mode": MODE,
                "tts_speaker": SPEAKER,
                "audio_path": str(audio_path),
                "sample_rate": sample_rate,
                "duration_seconds": duration_seconds,
                "chunk_count": chunk_count,
                "latency_seconds": round(time.time() - started, 3),
                "error": err,
            })
            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out_f.flush()
            print(
                f"[{i}/{len(rows)}] {pid} {row['case_id']} dur={duration_seconds} chunks={chunk_count} err={bool(err)}",
                flush=True,
            )


if __name__ == "__main__":
    main()
