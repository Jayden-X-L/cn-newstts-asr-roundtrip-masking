#!/usr/bin/env python3
"""Build a publication-safe Paraformer result bundle with relative paths."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mvp_eval/paraformer_targeted_20260717"
OUTPUT = SOURCE / "release_bundle"

JSONL_FILES = (
    "paraformer_full_220_manifest.jsonl",
    "paraformer_aligned_46_manifest.jsonl",
    "paraformer_full_220_results.jsonl",
    "paraformer_aligned_46_results.jsonl",
)
COPY_FILES = (
    "paraformer_experiment_manifest_summary.json",
    "paraformer_targeted_control_summary.json",
    "paraformer_targeted_control_summary.md",
    "paraformer_confirmed_97_transcript_audit.csv",
    "paraformer_confirmed_97_transcript_audit.html",
    "paraformer_aligned_46_transcript_audit.csv",
    "paraformer_aligned_46_transcript_audit.html",
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


def sanitize_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["audio_archive_path"] = archive_audio_path(row)
    output.pop("remote_audio_path", None)
    return output


def sanitize_jsonl(source: Path, destination: Path) -> int:
    count = 0
    with source.open(encoding="utf-8") as input_handle, destination.open(
        "w", encoding="utf-8"
    ) as output_handle:
        for line in input_handle:
            if not line.strip():
                continue
            output_handle.write(
                json.dumps(sanitize_row(json.loads(line)), ensure_ascii=False) + "\n"
            )
            count += 1
    return count


def assert_no_private_paths() -> None:
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
    OUTPUT.mkdir(parents=True, exist_ok=True)
    counts = {
        name: sanitize_jsonl(SOURCE / name, OUTPUT / name) for name in JSONL_FILES
    }
    for name in COPY_FILES:
        shutil.copy2(SOURCE / name, OUTPUT / name)

    readme = """# Paraformer-zh Targeted ASR Control

This bundle contains the independent Paraformer ASR control reported in the
paper. It uses FunASR `paraformer-zh` v2.0.4, which resolved to
`iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch`,
with FSMN-VAD v2.0.4. Inverse text normalization was disabled; no punctuation
model, hotwords, or external language model were used.

- Full Raw audio: 220/220 transcripts, zero inference errors.
- Previously human-confirmed wrong-and-masked subset: 97 cases.
- Occurrence-aware exact annotated surface recovery: 0/46 MiMo and 2/51
  CosyVoice cases.
- Aligned MiMo clips: 46/46 transcripts, zero inference errors and zero exact
  annotated surface recoveries.

The transcript audit is a cross-ASR control, not a replacement for human
listening. `audio_archive_path` points to the corresponding file in the
companion Zenodo archive; no workstation or local-machine path is retained.
"""
    (OUTPUT / "README.md").write_text(readme, encoding="utf-8")
    assert_no_private_paths()
    print(json.dumps({"output": str(OUTPUT), "jsonl_rows": counts}, indent=2))


if __name__ == "__main__":
    main()
