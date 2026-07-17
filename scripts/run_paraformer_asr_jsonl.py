#!/usr/bin/env python3
"""Run a resumable Paraformer ASR control from a JSONL manifest."""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path
from typing import Any

import funasr
import torch
from funasr import AutoModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--model", default="paraformer-zh")
    parser.add_argument("--model-revision", default="v2.0.4")
    parser.add_argument("--vad-model", default="fsmn-vad")
    parser.add_argument("--vad-revision", default="v2.0.4")
    parser.add_argument(
        "--use-itn",
        action="store_true",
        help=(
            "Pass use_itn=True to FunASR. Behavior is model-dependent; the "
            "paired Paraformer check in this project produced no transcript change."
        ),
    )
    parser.add_argument("--batch-size-s", type=int, default=120)
    parser.add_argument("--max-retries", type=int, default=2)
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def completed_item_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not str(row.get("error") or "").strip():
                completed.add(str(row.get("item_id") or ""))
    return completed


def extract_text(result: Any) -> str:
    if isinstance(result, list):
        pieces = [extract_text(item) for item in result]
        return "".join(piece for piece in pieces if piece).strip()
    if isinstance(result, dict):
        return str(result.get("text") or "").strip()
    return str(result or "").strip()


def extract_timestamps(result: Any) -> Any:
    if isinstance(result, list):
        values = [extract_timestamps(item) for item in result]
        return [value for value in values if value]
    if isinstance(result, dict):
        return result.get("timestamp") or result.get("sentence_info") or []
    return []


def main() -> None:
    args = parse_args()
    rows = load_jsonl(args.manifest)
    if len({str(row.get("item_id")) for row in rows}) != len(rows):
        raise RuntimeError("manifest item_id values must be unique")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    completed = completed_item_ids(args.output)
    protocol = {
        "asr_model": args.model,
        "asr_model_revision": args.model_revision,
        "vad_model": args.vad_model,
        "vad_model_revision": args.vad_revision,
        "device": args.device,
        "use_itn": args.use_itn,
        "punctuation_model": None,
        "hotword": None,
        "external_language_model": None,
        "batch_size_s": args.batch_size_s,
        "funasr_version": getattr(funasr, "__version__", "unknown"),
        "torch_version": torch.__version__,
        "python_version": platform.python_version(),
    }
    print(
        json.dumps(
            {
                **protocol,
                "manifest": str(args.manifest),
                "output": str(args.output),
                "rows": len(rows),
                "already_completed": len(completed),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )

    model = AutoModel(
        model=args.model,
        model_revision=args.model_revision,
        vad_model=args.vad_model,
        vad_model_revision=args.vad_revision,
        device=args.device,
        disable_update=True,
    )

    with args.output.open("a", encoding="utf-8") as output_handle:
        for index, row in enumerate(rows, 1):
            item_id = str(row["item_id"])
            if item_id in completed:
                continue

            audio_path = Path(str(row["remote_audio_path"]))
            error = ""
            asr_text = ""
            timestamps: Any = []
            attempts = 0
            started = time.time()
            if not audio_path.is_file():
                error = f"audio file not found: {audio_path}"
            else:
                for attempt in range(1, args.max_retries + 2):
                    attempts = attempt
                    try:
                        result = model.generate(
                            input=str(audio_path),
                            batch_size_s=args.batch_size_s,
                            use_itn=args.use_itn,
                        )
                        asr_text = extract_text(result)
                        timestamps = extract_timestamps(result)
                        if not asr_text:
                            raise RuntimeError("empty ASR transcript")
                        error = ""
                        break
                    except Exception as exc:  # Keep row-level failures resumable.
                        error = f"{type(exc).__name__}: {exc}"
                        if attempt <= args.max_retries:
                            time.sleep(min(2**attempt, 8))

            record = {
                **row,
                **protocol,
                "asr_protocol": (
                    "paraformer_plain_itn"
                    if args.use_itn
                    else "paraformer_plain_no_itn"
                ),
                "asr_text": asr_text,
                "asr_timestamps": timestamps,
                "attempts": attempts,
                "latency_seconds": round(time.time() - started, 3),
                "error": error,
            }
            output_handle.write(json.dumps(record, ensure_ascii=False) + "\n")
            output_handle.flush()
            print(
                f"[{index}/{len(rows)}] {item_id} "
                f"chars={len(asr_text)} attempts={attempts} error={bool(error)}",
                flush=True,
            )


if __name__ == "__main__":
    main()
