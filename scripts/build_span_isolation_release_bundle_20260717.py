#!/usr/bin/env python3
"""Build publication-safe reviewed CSVs for the span-isolation probe."""

from __future__ import annotations

import csv
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "mvp_eval" / "span_isolated_asr_probe_20260612"


def publication_path(column: str, value: str) -> str:
    if not value:
        return ""
    name = Path(value).name
    if column == "source_audio_path":
        return f"audio/mimo_v25_tts_p1p2_200/raw/{name}"
    if column == "clip_audio_path" and "aligned" in value:
        return f"audio/span_isolation_aligned_clips/{name}"
    if column == "clip_audio_path":
        return f"audio/span_isolation_iso6s/{name}"
    return name


def sanitize_csv(source: Path, destination: Path) -> None:
    with source.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = reader.fieldnames or []
    for row in rows:
        for column in columns:
            if column.endswith("_path"):
                row[column] = publication_path(column, row.get(column, ""))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    output = Path(
        os.environ.get(
            "SPAN_ISOLATION_RELEASE_DIR",
            ROOT / "release_packages_20260616/github_cn_newstts_asr_roundtrip/results/span_isolation",
        )
    )
    output.mkdir(parents=True, exist_ok=True)
    sanitize_csv(
        SOURCE / "outputs/mimo_strict_aligned_whisper_ts_results.reviewed.csv",
        output / "mimo_strict_aligned_46_reviewed.csv",
    )
    sanitize_csv(
        SOURCE / "outputs/mimo_strict_span_iso_6s_results.reviewed.csv",
        output / "mimo_strict_rough_6s_46_reviewed.csv",
    )
    for name in (
        "span_isolated_asr_probe_reviewed_summary_aligned_whisper_ts_20260612.md",
        "table_full_vs_rough_vs_aligned_asr_probe_20260612.md",
    ):
        shutil.copy2(SOURCE / name, output / name)
    print(f"output={output}")


if __name__ == "__main__":
    main()
