#!/usr/bin/env python3
"""Build a publication-safe Qwen3-ASR result bundle with relative paths."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mvp_eval/paraformer_itn_qwen3_20260717"
OUTPUT = SOURCE / "qwen3_release_bundle"

JSONL_FILES = (
    "qwen3_asr_1p7b_full_220_results.jsonl",
    "qwen3_asr_1p7b_aligned_46_results.jsonl",
)
COPY_FILES = (
    "qwen3_asr_1p7b_control_summary.json",
    "qwen3_asr_1p7b_control_summary.md",
    "qwen3_confirmed_97_review_overrides.json",
    "qwen3_confirmed_97_transcript_audit.csv",
    "qwen3_confirmed_97_transcript_audit.html",
    "qwen3_aligned_46_transcript_audit.csv",
)


def archive_audio_path(row: dict[str, Any]) -> str:
    audio_name = Path(str(row["remote_audio_path"])).name
    if row.get("audio_scope") == "aligned_span_clip":
        return f"audio/span_isolation_aligned_clips/{audio_name}"
    if row.get("tts_system") == "MiMo-V2.5-TTS API":
        return f"audio/mimo_v25_tts_p1p2_200/raw/{audio_name}"
    if row.get("tts_system") == "CosyVoice-300M-SFT":
        return f"audio/cosyvoice_targeted_raw_110/raw_110/{audio_name}"
    raise ValueError(f"unknown audio mapping for {row.get('item_id')}")


def sanitize_jsonl(source: Path, destination: Path) -> int:
    count = 0
    with source.open(encoding="utf-8") as input_handle, destination.open(
        "w", encoding="utf-8"
    ) as output_handle:
        for line in input_handle:
            if not line.strip():
                continue
            row = json.loads(line)
            row["audio_archive_path"] = archive_audio_path(row)
            row.pop("remote_audio_path", None)
            output_handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            count += 1
    return count


def assert_publication_safe() -> None:
    forbidden = ("/" + "data/ai/", "/" + "Users/")
    for path in OUTPUT.rglob("*"):
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for token in forbidden:
            if token in content:
                raise RuntimeError(f"forbidden token {token!r} in {path}")


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    counts = {
        name: sanitize_jsonl(SOURCE / name, OUTPUT / name) for name in JSONL_FILES
    }
    for name in COPY_FILES:
        shutil.copy2(SOURCE / name, OUTPUT / name)

    readme = """# Qwen3-ASR-1.7B Targeted ASR Control

This bundle contains the open-source Qwen3-ASR control reported in the paper.
The local Transformers backend uses an empty context, automatic language
detection, BF16/SDPA inference, and the package-default deterministic decode.
No source text, expected reading, negative reading, hotword, or target-specific
hint is supplied to the model.

- Full Raw audio: 220/220 transcripts, zero inference errors.
- Human-confirmed wrong-reading subset: 97 files.
- Occurrence-aware surface-correct recovery: 19/46 MiMo, 21/51 CosyVoice, and
  40/97 overall.
- On the 19 full-context MiMo surface recoveries, aligned-span transcription
  re-exposes a wrong or noncanonical form in 12 and leaves 7 surface-correct.

The review override file records only transcript cases that require semantic,
occurrence-aware adjudication; predefined negative-only matches are assigned
directly by the analysis script. `audio_archive_path` points to the companion
Zenodo archive, and no workstation or local-machine path is retained.
"""
    (OUTPUT / "README.md").write_text(readme, encoding="utf-8")
    assert_publication_safe()
    print(json.dumps({"output": str(OUTPUT), "jsonl_rows": counts}, indent=2))


if __name__ == "__main__":
    main()
