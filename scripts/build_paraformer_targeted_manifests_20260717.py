#!/usr/bin/env python3
"""Freeze manifests for the Paraformer targeted ASR control.

The full-audio manifest contains the same 110 MiMo and 110 CosyVoice Raw
items that already have human audit labels.  The aligned manifest contains
the 46 MiMo clips used by the context-isolation diagnostic.
"""

from __future__ import annotations

import csv
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "mvp_eval/paraformer_targeted_20260717"

MIMO_LABELS = (
    ROOT
    / "mvp_eval/paper_assets_20260608/"
    "targeted_masked_error_audit_yield_review_results_final_20260612.csv"
)
COSY_LABELS = (
    ROOT
    / "mvp_eval/cosyvoice_targeted_20260608/human_labels_20260614/"
    "cosyvoice_raw_110_human_review_labels_final_20260614.csv"
)
COSY_MANIFEST = (
    ROOT
    / "mvp_eval/cosyvoice_targeted_20260608/"
    "cosyvoice_targeted_raw_110_manifest_20260608.jsonl"
)
ALIGNED_MANIFEST = (
    ROOT
    / "mvp_eval/span_isolated_asr_probe_20260612/aligned_whisper_ts/"
    "aligned_manifest_whisper_ts_46.jsonl"
)

REMOTE_MIMO_AUDIO = Path(
    os.environ.get(
        "PARAFORMER_MIMO_AUDIO_DIR", "audio/mimo_v25_tts_p1p2_200/raw"
    )
)
REMOTE_COSY_AUDIO = Path(
    os.environ.get(
        "PARAFORMER_COSY_AUDIO_DIR", "audio/cosyvoice_targeted_raw_110/raw_110"
    )
)
REMOTE_ALIGNED_AUDIO = Path(
    os.environ.get(
        "PARAFORMER_ALIGNED_AUDIO_DIR", "audio/span_isolation_aligned_clips"
    )
)


def text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def split_negative_readings(risk_span_lines: str, target_span: str) -> list[str]:
    negatives: list[str] = []
    for line in text(risk_span_lines).splitlines():
        left, marker, right = line.partition("=>")
        if not marker or text(left) != text(target_span):
            continue
        _, wrong_marker, wrong = right.partition("|wrong:")
        if wrong_marker:
            negatives.extend(text(item) for item in wrong.split("/") if text(item))
    return negatives


def unique_nonempty(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        item = text(value)
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def mimo_full_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in read_csv(MIMO_LABELS):
        probe_id = text(source["probe_candidate_id"])
        case_id = text(source["case_id"])
        outcome = text(source.get("final_audit_outcome")) or text(
            source.get("audit_outcome")
        )
        target = text(source.get("target_span"))
        expected = text(source.get("expected_reading"))
        actual = text(source.get("raw_tts_actual_reading"))
        negatives = split_negative_readings(text(source.get("risk_span_lines")), target)
        rows.append(
            {
                "item_id": f"mimo_full_{probe_id}",
                "audio_scope": "full_sentence",
                "tts_system": "MiMo-V2.5-TTS API",
                "probe_candidate_id": probe_id,
                "case_id": case_id,
                "freeze_id": text(source.get("freeze_id")),
                "source": text(source.get("source")),
                "domain": text(source.get("domain")),
                "cdrd_label": text(source.get("cdrd_label")),
                "primary_type": text(source.get("primary_type")),
                "human_audit_outcome": outcome,
                "target_span": target,
                "expected_reading": expected,
                "human_heard_reading": actual,
                "negative_readings": unique_nonempty([actual, *negatives]),
                "risk_span_lines": text(source.get("risk_span_lines")),
                "input_text": text(source.get("raw_text")),
                "remote_audio_path": str(REMOTE_MIMO_AUDIO / f"{case_id}.wav"),
            }
        )
    return rows


def cosy_full_rows() -> list[dict[str, Any]]:
    label_rows = read_csv(COSY_LABELS)
    source_by_probe = {
        text(row["probe_candidate_id"]): row for row in read_jsonl(COSY_MANIFEST)
    }
    rows: list[dict[str, Any]] = []
    for label in label_rows:
        probe_id = text(label["probe_candidate_id"])
        source = source_by_probe[probe_id]
        case_id = text(label["case_id"])
        target = text(label.get("target_span_review")) or text(
            source.get("target_span")
        )
        expected = text(label.get("expected_reading_review")) or text(
            source.get("expected_reading")
        )
        actual = text(label.get("cosyvoice_heard_reading"))
        negatives = split_negative_readings(text(source.get("risk_span_lines")), target)
        audio_name = Path(text(label.get("audio_path"))).name
        rows.append(
            {
                "item_id": f"cosyvoice_full_{probe_id}",
                "audio_scope": "full_sentence",
                "tts_system": "CosyVoice-300M-SFT",
                "probe_candidate_id": probe_id,
                "case_id": case_id,
                "freeze_id": text(label.get("freeze_id")),
                "source": text(label.get("source")),
                "domain": text(label.get("domain")),
                "cdrd_label": text(label.get("cdrd_label")),
                "primary_type": text(label.get("primary_type")),
                "human_audit_outcome": text(label.get("cosyvoice_outcome")),
                "target_span": target,
                "expected_reading": expected,
                "human_heard_reading": actual,
                "negative_readings": unique_nonempty([actual, *negatives]),
                "risk_span_lines": text(source.get("risk_span_lines")),
                "input_text": text(source.get("tts_input_text")),
                "remote_audio_path": str(REMOTE_COSY_AUDIO / audio_name),
            }
        )
    return rows


def aligned_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for source in read_jsonl(ALIGNED_MANIFEST):
        probe_id = text(source["probe_candidate_id"])
        clip_name = Path(text(source["aligned_clip_audio_path"])).name
        rows.append(
            {
                "item_id": f"mimo_aligned_{probe_id}",
                "audio_scope": "aligned_span_clip",
                "tts_system": "MiMo-V2.5-TTS API",
                "probe_candidate_id": probe_id,
                "case_id": text(source.get("case_id")),
                "freeze_id": text(source.get("freeze_id")),
                "cdrd_label": text(source.get("cdrd_label")),
                "primary_type": text(source.get("primary_type")),
                "human_audit_outcome": "confirmed masked",
                "target_span": text(source.get("target_span")),
                "expected_reading": text(source.get("expected_reading")),
                "human_heard_reading": text(source.get("raw_tts_actual_reading")),
                "negative_readings": unique_nonempty(
                    list(source.get("negative_readings") or [])
                ),
                "alignment_model": text(source.get("alignment_model")),
                "alignment_method": text(source.get("alignment_method")),
                "aligned_clip_start_seconds": source.get("aligned_clip_start_seconds"),
                "aligned_clip_end_seconds": source.get("aligned_clip_end_seconds"),
                "remote_audio_path": str(REMOTE_ALIGNED_AUDIO / clip_name),
            }
        )
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "rows": len(rows),
        "tts_systems": dict(Counter(row["tts_system"] for row in rows)),
        "audio_scopes": dict(Counter(row["audio_scope"] for row in rows)),
        "human_audit_outcomes": dict(
            Counter(row["human_audit_outcome"] for row in rows)
        ),
        "confirmed_with_target_and_expected": sum(
            row["human_audit_outcome"] == "confirmed masked"
            and bool(row["target_span"])
            and bool(row["expected_reading"])
            for row in rows
        ),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    full = mimo_full_rows() + cosy_full_rows()
    aligned = aligned_rows()

    if len(full) != 220:
        raise RuntimeError(f"expected 220 full rows, found {len(full)}")
    if len({row["item_id"] for row in full}) != 220:
        raise RuntimeError("full manifest item_id values are not unique")
    if len(aligned) != 46:
        raise RuntimeError(f"expected 46 aligned rows, found {len(aligned)}")
    if sum(row["human_audit_outcome"] == "confirmed masked" for row in full) != 97:
        raise RuntimeError("expected 97 previously confirmed masked full-audio rows")

    full_path = OUT_DIR / "paraformer_full_220_manifest.jsonl"
    aligned_path = OUT_DIR / "paraformer_aligned_46_manifest.jsonl"
    write_jsonl(full_path, full)
    write_jsonl(aligned_path, aligned)

    summary = {
        "purpose": (
            "Independent Paraformer-zh ASR control on existing human-audited "
            "MiMo and CosyVoice Raw audio."
        ),
        "full_manifest": summarize(full),
        "aligned_manifest": summarize(aligned),
        "primary_analysis_boundary": (
            "Cross-ASR masking recurrence is evaluated on the 97 full-audio "
            "cases previously confirmed by human listening to contain a wrong "
            "TTS reading. All 220 transcripts are retained for audit."
        ),
        "asr_protocol": {
            "model_alias": "paraformer-zh",
            "model_revision": "v2.0.4",
            "vad_model": "fsmn-vad",
            "vad_revision": "v2.0.4",
            "inverse_text_normalization": False,
            "punctuation_model": None,
            "hotword": None,
            "external_language_model": None,
        },
    }
    summary_path = OUT_DIR / "paraformer_experiment_manifest_summary.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(full_path)
    print(aligned_path)


if __name__ == "__main__":
    main()
