"""Create aligned risk-span clips using Whisper-small word timestamps.

This is a lightweight forced-alignment-style pass for the 46 confirmed MiMo
masked-error cases. It uses Whisper timestamps to refine the risk-span window
before rerunning isolated ASR.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from transformers import pipeline


ROOT = Path(os.environ.get("SPAN_ALIGN_ROOT", "/data/ai/workspace/cn_newstts/span_alignment_probe_20260612"))
MANIFEST = Path(os.environ.get("SPAN_ALIGN_MANIFEST", str(ROOT / "manifest_span_iso_6s_46.jsonl")))
OUT_DIR = Path(os.environ.get("SPAN_ALIGN_OUT_DIR", str(ROOT / "aligned_whisper_ts")))
AUDIO_BASE = Path(os.environ.get("SPAN_ALIGN_AUDIO_BASE", str(ROOT / "local_project_files")))
MODEL_ID = os.environ.get("WHISPER_MODEL_ID", "openai/whisper-small")
HF_HOME = os.environ.get("HF_HOME", "/data/ai/hf_cache")
PADDING_SECONDS = float(os.environ.get("SPAN_ALIGN_PADDING_SECONDS", "0.8"))
MIN_CLIP_SECONDS = float(os.environ.get("SPAN_ALIGN_MIN_CLIP_SECONDS", "3.0"))


ZH_DIGITS = {
    "0": "零",
    "1": "一",
    "2": "二",
    "3": "三",
    "4": "四",
    "5": "五",
    "6": "六",
    "7": "七",
    "8": "八",
    "9": "九",
}


def norm(text: object) -> str:
    s = str(text or "").lower()
    s = s.replace("－", "-").replace("—", "-").replace("–", "-").replace("−", "-")
    for ch in " \t\r\n，。！？、；：,.!?;:（）()[]【】「」『』《》“”\"'`·/":
        s = s.replace(ch, "")
    return s


def digit_by_digit(text: str) -> str:
    return "".join(ZH_DIGITS.get(ch, ch) for ch in str(text))


def candidate_strings(row: dict) -> list[str]:
    vals = [
        row.get("target_span"),
        row.get("expected_reading"),
        row.get("raw_tts_actual_reading"),
    ]
    for val in row.get("negative_readings") or []:
        vals.append(val)

    target = str(row.get("target_span") or "")
    if target:
        vals.append(digit_by_digit(target))
        vals.append(target.replace("-", "杠"))
        vals.append(digit_by_digit(target.replace("-", "杠")))
        vals.append(target.replace("-", "负"))
        vals.append(digit_by_digit(target.replace("-", "负")))
        vals.append(target.replace("-", "至"))
        vals.append(digit_by_digit(target.replace("-", "至")))
        vals.append(target.replace("-", "比"))
        vals.append(digit_by_digit(target.replace("-", "比")))
        vals.append(target.replace("kW", "KW").replace("kw", "KW"))
        vals.append(digit_by_digit(target.replace("kW", "KW").replace("kw", "KW")))
    out = []
    seen = set()
    for val in vals:
        val = str(val or "").strip()
        nv = norm(val)
        if nv and nv not in seen:
            seen.add(nv)
            out.append(val)
    return out


def load_rows() -> list[dict]:
    rows = []
    with MANIFEST.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def remote_audio_path(row: dict) -> Path:
    # Manifest paths are absolute local Mac paths. Use case_id under the synced
    # local_project_files mirror on the workstation.
    case_id = row["case_id"]
    return AUDIO_BASE / "mvp_eval" / "audio" / "raw" / f"{case_id}.wav"


def completed(path: Path) -> set[str]:
    if not path.exists():
        return set()
    out = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except Exception:
                continue
            out.add(str(row.get("probe_candidate_id")))
    return out


def build_char_timeline(chunks: list[dict]) -> tuple[str, list[tuple[float, float]]]:
    chars: list[str] = []
    times: list[tuple[float, float]] = []
    for chunk in chunks:
        text = str(chunk.get("text") or "")
        ts = chunk.get("timestamp") or chunk.get("timestamps") or [None, None]
        start, end = ts[0], ts[1]
        if start is None or end is None:
            continue
        try:
            start = float(start)
            end = float(end)
        except Exception:
            continue
        if end <= start:
            continue
        raw_chars = [ch for ch in text if norm(ch)]
        n = max(1, len(raw_chars))
        j = 0
        for ch in text:
            nch = norm(ch)
            if not nch:
                continue
            c_start = start + (end - start) * (j / n)
            c_end = start + (end - start) * ((j + 1) / n)
            chars.append(nch)
            times.append((c_start, c_end))
            j += 1
    return "".join(chars), times


def find_aligned_window(row: dict, chunks: list[dict]) -> dict:
    concat, times = build_char_timeline(chunks)
    rough_center = float(row.get("span_center_seconds_est") or 0)
    matches = []
    for cand in candidate_strings(row):
        nc = norm(cand)
        if not nc:
            continue
        start = 0
        while True:
            idx = concat.find(nc, start)
            if idx < 0:
                break
            end_idx = idx + len(nc) - 1
            if idx < len(times) and end_idx < len(times):
                s = times[idx][0]
                e = times[end_idx][1]
                center = (s + e) / 2
                matches.append({
                    "method": "candidate_match",
                    "candidate": cand,
                    "norm_candidate": nc,
                    "char_index": idx,
                    "match_start": s,
                    "match_end": e,
                    "distance_to_rough_center": abs(center - rough_center),
                })
            start = idx + 1
    if matches:
        matches.sort(key=lambda m: (m["distance_to_rough_center"], -(m["match_end"] - m["match_start"])))
        return matches[0]

    # Fallback: use the chunk whose midpoint is closest to the rough center.
    fallback = None
    for chunk in chunks:
        ts = chunk.get("timestamp") or [None, None]
        if ts[0] is None or ts[1] is None:
            continue
        s, e = float(ts[0]), float(ts[1])
        if e <= s:
            continue
        center = (s + e) / 2
        item = {
            "method": "nearest_chunk_fallback",
            "candidate": "",
            "norm_candidate": "",
            "chunk_text": chunk.get("text", ""),
            "match_start": s,
            "match_end": e,
            "distance_to_rough_center": abs(center - rough_center),
        }
        if fallback is None or item["distance_to_rough_center"] < fallback["distance_to_rough_center"]:
            fallback = item
    if fallback:
        return fallback

    return {
        "method": "rough_center_fallback",
        "candidate": "",
        "norm_candidate": "",
        "match_start": max(0.0, rough_center - MIN_CLIP_SECONDS / 2),
        "match_end": rough_center + MIN_CLIP_SECONDS / 2,
        "distance_to_rough_center": 0.0,
    }


def cut_clip(audio: np.ndarray, sr: int, start: float, end: float, duration: float) -> tuple[np.ndarray, float, float]:
    start = max(0.0, start - PADDING_SECONDS)
    end = min(duration, end + PADDING_SECONDS)
    if end - start < MIN_CLIP_SECONDS:
        center = (start + end) / 2
        start = max(0.0, center - MIN_CLIP_SECONDS / 2)
        end = min(duration, start + MIN_CLIP_SECONDS)
        start = max(0.0, end - MIN_CLIP_SECONDS)
    s_idx = max(0, int(round(start * sr)))
    e_idx = min(len(audio), int(round(end * sr)))
    return audio[s_idx:e_idx], start, end


def main() -> None:
    os.environ["HF_HOME"] = HF_HOME
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    clips_dir = OUT_DIR / "clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    out_jsonl = OUT_DIR / "aligned_manifest_whisper_ts_46.jsonl"
    done = completed(out_jsonl)
    rows = load_rows()
    device = 0 if torch.cuda.is_available() else -1
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    print(json.dumps({
        "model": MODEL_ID,
        "device": str(device),
        "rows": len(rows),
        "already_done": len(done),
        "out": str(out_jsonl),
    }, ensure_ascii=False), flush=True)
    asr = pipeline("automatic-speech-recognition", model=MODEL_ID, device=device, torch_dtype=dtype)

    with out_jsonl.open("a", encoding="utf-8") as out_f:
        for i, row in enumerate(rows, 1):
            pid = str(row["probe_candidate_id"])
            if pid in done:
                print(f"[{i}/{len(rows)}] {pid} skipped", flush=True)
                continue
            error = ""
            rec = dict(row)
            try:
                audio_path = remote_audio_path(row)
                audio, sr = sf.read(str(audio_path), dtype="float32")
                if audio.ndim > 1:
                    audio = audio.mean(axis=1)
                duration = len(audio) / sr
                result = asr(
                    {"array": audio, "sampling_rate": sr},
                    generate_kwargs={"language": "zh", "task": "transcribe"},
                    return_timestamps="word",
                )
                chunks = result.get("chunks") or []
                match = find_aligned_window(row, chunks)
                clip_audio, clip_start, clip_end = cut_clip(audio, sr, match["match_start"], match["match_end"], duration)
                target = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "_", str(row.get("target_span") or "target"))
                clip_path = clips_dir / f"{pid}_{row['case_id']}_{target}_aligned.wav"
                sf.write(str(clip_path), clip_audio, sr)
                rec.update({
                    "alignment_model": MODEL_ID,
                    "alignment_method": match.get("method"),
                    "alignment_candidate": match.get("candidate"),
                    "alignment_chunk_text": match.get("chunk_text", ""),
                    "alignment_match_start_seconds": round(float(match["match_start"]), 3),
                    "alignment_match_end_seconds": round(float(match["match_end"]), 3),
                    "alignment_distance_to_rough_center": round(float(match.get("distance_to_rough_center", 0)), 3),
                    "aligned_clip_start_seconds": round(clip_start, 3),
                    "aligned_clip_end_seconds": round(clip_end, 3),
                    "aligned_clip_duration_seconds": round(clip_end - clip_start, 3),
                    "aligned_clip_audio_path": str(clip_path),
                    "alignment_transcript_text": result.get("text", ""),
                    "alignment_chunks_json": json.dumps(chunks, ensure_ascii=False),
                    "error": "",
                })
            except Exception as exc:
                error = repr(exc)
                rec.update({"error": error})
            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out_f.flush()
            print(f"[{i}/{len(rows)}] {pid} {rec.get('alignment_method', 'error')} err={bool(error)}", flush=True)


if __name__ == "__main__":
    main()
