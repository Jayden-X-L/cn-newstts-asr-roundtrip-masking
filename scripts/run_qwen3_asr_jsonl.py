#!/usr/bin/env python3
"""Run resumable, context-free Qwen3-ASR transcription from a JSONL manifest."""

from __future__ import annotations

import argparse
import json
import platform
import time
from pathlib import Path
from typing import Any

import torch
from qwen_asr import Qwen3ASRModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", default="Qwen/Qwen3-ASR-1.7B")
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--input-batch-size", type=int, default=4)
    parser.add_argument("--inference-batch-size", type=int, default=4)
    parser.add_argument("--max-new-tokens", type=int, default=1024)
    parser.add_argument("--max-retries", type=int, default=1)
    parser.add_argument("--attn-implementation", default="sdpa")
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


def package_version(package_name: str) -> str:
    try:
        from importlib.metadata import version

        return version(package_name)
    except Exception:
        return "unknown"


def extract_result(result: Any) -> tuple[str, str]:
    text = str(getattr(result, "text", "") or "").strip()
    language = str(getattr(result, "language", "") or "").strip()
    return text, language


def transcribe_batch(
    model: Qwen3ASRModel,
    rows: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    paths = [str(row["remote_audio_path"]) for row in rows]
    results = model.transcribe(
        audio=paths,
        context="",
        language=None,
        return_time_stamps=False,
    )
    if len(results) != len(rows):
        raise RuntimeError(f"result count mismatch: {len(results)} != {len(rows)}")
    values = [extract_result(result) for result in results]
    if any(not text for text, _ in values):
        raise RuntimeError("empty ASR transcript in batch")
    return values


def main() -> None:
    args = parse_args()
    if args.input_batch_size < 1 or args.inference_batch_size < 1:
        raise ValueError("batch sizes must be positive")

    rows = load_jsonl(args.manifest)
    if len({str(row.get("item_id")) for row in rows}) != len(rows):
        raise RuntimeError("manifest item_id values must be unique")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    completed = completed_item_ids(args.output)
    model_load_path = str(args.model_path or args.model)
    protocol = {
        "asr_model": args.model,
        "asr_model_source": args.model,
        "loaded_from_local_cache": args.model_path is not None,
        "backend": "qwen-asr-transformers",
        "device": args.device,
        "dtype": "bfloat16",
        "attention_implementation": args.attn_implementation,
        "context": "",
        "language_constraint": None,
        "return_time_stamps": False,
        "decoding": "deterministic_package_default",
        "input_batch_size": args.input_batch_size,
        "inference_batch_size": args.inference_batch_size,
        "max_new_tokens": args.max_new_tokens,
        "qwen_asr_version": package_version("qwen-asr"),
        "transformers_version": package_version("transformers"),
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

    model = Qwen3ASRModel.from_pretrained(
        model_load_path,
        dtype=torch.bfloat16,
        device_map=args.device,
        attn_implementation=args.attn_implementation,
        max_inference_batch_size=args.inference_batch_size,
        max_new_tokens=args.max_new_tokens,
    )

    pending = [row for row in rows if str(row["item_id"]) not in completed]
    with args.output.open("a", encoding="utf-8") as output_handle:
        for batch_start in range(0, len(pending), args.input_batch_size):
            batch = pending[batch_start : batch_start + args.input_batch_size]
            valid: list[dict[str, Any]] = []
            missing: list[dict[str, Any]] = []
            for row in batch:
                if Path(str(row["remote_audio_path"])).is_file():
                    valid.append(row)
                else:
                    missing.append(row)

            records: list[dict[str, Any]] = []
            for row in missing:
                records.append(
                    {
                        **row,
                        **protocol,
                        "asr_protocol": "qwen3_asr_1p7b_plain",
                        "asr_text": "",
                        "detected_language": "",
                        "attempts": 0,
                        "latency_seconds": 0.0,
                        "error": f"audio file not found: {row['remote_audio_path']}",
                    }
                )

            if valid:
                started = time.time()
                values: list[tuple[str, str]] = []
                error = ""
                attempts = 0
                for attempt in range(1, args.max_retries + 2):
                    attempts = attempt
                    try:
                        values = transcribe_batch(model, valid)
                        error = ""
                        break
                    except Exception as exc:
                        error = f"{type(exc).__name__}: {exc}"
                        if attempt <= args.max_retries:
                            time.sleep(min(2**attempt, 8))

                elapsed = time.time() - started
                if error and len(valid) > 1:
                    values = []
                    for row in valid:
                        row_started = time.time()
                        row_error = ""
                        row_values: list[tuple[str, str]] = []
                        row_attempts = 0
                        for attempt in range(1, args.max_retries + 2):
                            row_attempts = attempt
                            try:
                                row_values = transcribe_batch(model, [row])
                                row_error = ""
                                break
                            except Exception as exc:
                                row_error = f"{type(exc).__name__}: {exc}"
                                if attempt <= args.max_retries:
                                    time.sleep(min(2**attempt, 8))
                        text, language = row_values[0] if row_values else ("", "")
                        records.append(
                            {
                                **row,
                                **protocol,
                                "asr_protocol": "qwen3_asr_1p7b_plain",
                                "asr_text": text,
                                "detected_language": language,
                                "attempts": row_attempts,
                                "latency_seconds": round(time.time() - row_started, 3),
                                "error": row_error,
                            }
                        )
                else:
                    per_row_latency = elapsed / max(len(valid), 1)
                    for row, (text, language) in zip(valid, values):
                        records.append(
                            {
                                **row,
                                **protocol,
                                "asr_protocol": "qwen3_asr_1p7b_plain",
                                "asr_text": text,
                                "detected_language": language,
                                "attempts": attempts,
                                "latency_seconds": round(per_row_latency, 3),
                                "error": error,
                            }
                        )

            for record in records:
                output_handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                output_handle.flush()
                print(
                    f"[{len(completed) + 1}/{len(rows)}] {record['item_id']} "
                    f"chars={len(record['asr_text'])} error={bool(record['error'])}",
                    flush=True,
                )
                if not record["error"]:
                    completed.add(str(record["item_id"]))


if __name__ == "__main__":
    main()
