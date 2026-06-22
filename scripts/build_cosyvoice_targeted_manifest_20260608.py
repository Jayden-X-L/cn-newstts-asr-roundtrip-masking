#!/usr/bin/env python3
"""Build the 110-row CosyVoice targeted Raw-only manifest."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path("PROJECT_ROOT_PLACEHOLDER")
SOURCE = ROOT / "mvp_eval/paper_assets_20260608/targeted_masked_error_audit_yield_110_20260608.csv"
OUT_DIR = ROOT / "mvp_eval/cosyvoice_targeted_20260608"
OUT_JSONL = OUT_DIR / "cosyvoice_targeted_raw_110_manifest_20260608.jsonl"
OUT_SMOKE_JSONL = OUT_DIR / "cosyvoice_targeted_raw_smoke3_manifest_20260608.jsonl"
OUT_SUMMARY = OUT_DIR / "cosyvoice_targeted_raw_manifest_summary_20260608.json"


def norm(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    text = str(value)
    return "" if text.lower() == "nan" else text


def row_to_manifest(row: pd.Series) -> dict[str, Any]:
    text = norm(row.get("raw_text"))
    if not text:
        raise ValueError(f"Empty raw_text for {row.get('probe_candidate_id')}")
    return {
        "probe_candidate_id": norm(row.get("probe_candidate_id")),
        "case_id": norm(row.get("case_id")),
        "freeze_id": norm(row.get("freeze_id")),
        "source": norm(row.get("source")),
        "domain": norm(row.get("domain")),
        "cdrd_label": norm(row.get("cdrd_label")),
        "primary_type": norm(row.get("primary_type")),
        "pipeline": "raw",
        "tts_input_text": text,
        "raw_title": norm(row.get("raw_title")),
        "raw_summary": norm(row.get("raw_summary")),
        "target_span": norm(row.get("target_span")),
        "expected_reading": norm(row.get("expected_reading")),
        "mimo_raw_tts_actual_reading": norm(row.get("raw_tts_actual_reading")),
        "mimo_asr_masking_evidence": norm(row.get("asr_masking_evidence")),
        "mimo_audit_outcome": norm(row.get("audit_outcome")),
        "mimo_masking_type": norm(row.get("masking_type")),
        "matched_types": norm(row.get("matched_types")),
        "matched_spans": norm(row.get("matched_spans")),
        "risk_span_lines": norm(row.get("risk_span_lines")),
        "mimo_raw_auto_acc": row.get("raw_auto_acc"),
        "mimo_structured_auto_acc": row.get("structured_auto_acc"),
        "mimo_auto_delta_structured_minus_raw": row.get("auto_delta_structured_minus_raw"),
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(SOURCE)
    if len(df) != 110:
        raise ValueError(f"Expected 110 rows, got {len(df)}")
    rows = [row_to_manifest(row) for _, row in df.iterrows()]

    confirmed = [r for r in rows if r["mimo_audit_outcome"] == "confirmed masked"]
    needs_label = [r for r in rows if not r["mimo_audit_outcome"]]
    smoke = confirmed[:2] + needs_label[:1]
    if len(smoke) != 3:
        smoke = rows[:3]

    write_jsonl(OUT_JSONL, rows)
    write_jsonl(OUT_SMOKE_JSONL, smoke)

    summary = {
        "rows": len(rows),
        "smoke_rows": len(smoke),
        "source_csv": str(SOURCE),
        "manifest": str(OUT_JSONL),
        "smoke_manifest": str(OUT_SMOKE_JSONL),
        "mimo_confirmed_masked_in_manifest": len(confirmed),
        "mimo_needs_label_in_manifest": len(needs_label),
        "primary_type_counts": df["primary_type"].value_counts().to_dict(),
        "planned_tts": {
            "system": "CosyVoice",
            "model": "CosyVoice-300M-SFT",
            "speaker": "中文女",
            "mode": "sft",
            "pipeline": "raw_only",
        },
    }
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
