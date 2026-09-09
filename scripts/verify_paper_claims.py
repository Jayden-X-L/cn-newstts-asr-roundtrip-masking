#!/usr/bin/env python3
"""Verify original audit records and current boundary-corrected clip claims."""

from __future__ import annotations

import csv
import json
import runpy
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load_csv(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_json(path: str) -> dict[str, Any]:
    with (ROOT / path).open(encoding="utf-8") as handle:
        return json.load(handle)


def require_equal(label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, found {actual!r}")
    print(f"PASS {label}: {actual}")


def rounded(value: Any) -> float:
    return round(float(value), 4)


def binary_kappa(left: list[bool], right: list[bool]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("kappa inputs must be non-empty and have equal length")
    observed = sum(a == b for a, b in zip(left, right)) / len(left)
    left_positive = sum(left) / len(left)
    right_positive = sum(right) / len(right)
    expected = (
        left_positive * right_positive
        + (1 - left_positive) * (1 - right_positive)
    )
    if expected == 1:
        return 1.0
    return (observed - expected) / (1 - expected)


def main() -> int:
    mimo_rows = load_csv(
        "labels/targeted_audit_110/"
        "targeted_masked_error_audit_yield_review_results_final_20260612.csv"
    )
    mimo_counts = Counter(row["public_audit_outcome"].strip() for row in mimo_rows)
    require_equal(
        "MiMo targeted audit",
        {
            "confirmed masked": mimo_counts["confirmed masked"],
            "exposed TTS error": mimo_counts["exposed TTS error"],
            "no Raw TTS error": mimo_counts["no Raw TTS error"],
            "total": len(mimo_rows),
        },
        {
            "confirmed masked": 46,
            "exposed TTS error": 9,
            "no Raw TTS error": 55,
            "total": 110,
        },
    )

    cosy_rows = load_csv(
        "labels/cosyvoice_110/"
        "cosyvoice_raw_110_human_review_labels_final_20260614.csv"
    )
    cosy_counts = Counter(row["cosyvoice_outcome"].strip() for row in cosy_rows)
    require_equal(
        "CosyVoice targeted audit",
        {
            "confirmed masked": cosy_counts["confirmed masked"],
            "exposed TTS error": cosy_counts["exposed TTS error"],
            "no Raw TTS error": cosy_counts["no Raw TTS error"],
            "uncertain": cosy_counts["uncertain"],
            "not judgeable": cosy_counts["not judgeable"],
            "total": len(cosy_rows),
        },
        {
            "confirmed masked": 51,
            "exposed TTS error": 27,
            "no Raw TTS error": 30,
            "uncertain": 1,
            "not judgeable": 1,
            "total": 110,
        },
    )

    isolation_rows = load_csv(
        "results/span_isolation/mimo_strict_aligned_46_reviewed.csv"
    )
    isolation_counts = Counter(
        row["reviewed_isolated_asr_label"].strip() for row in isolation_rows
    )
    require_equal(
        "historical pre-repair aligned span-isolation audit (superseded by v1.0.4)",
        {
            "exposed": isolation_counts["exposed"],
            "still_masked": isolation_counts["still_masked"],
            "no_output": isolation_counts["no_output"],
            "other_transcript": isolation_counts["other_transcript"],
            "total": len(isolation_rows),
        },
        {
            "exposed": 18,
            "still_masked": 12,
            "no_output": 13,
            "other_transcript": 3,
            "total": 46,
        },
    )

    qwen = load_json("results/qwen3_asr/qwen3_asr_1p7b_control_summary.json")
    qwen_counts = qwen["reviewed_relation_counts"]
    require_equal(
        "Qwen3-ASR surface recovery",
        {
            "recovered": qwen_counts["exact_surface_correct_recovery"],
            "denominator": qwen["previously_labeled_confirmed_masked_rows"],
        },
        {"recovered": 40, "denominator": 97},
    )

    paraformer = load_json(
        "results/paraformer/paraformer_targeted_control_summary.json"
    )
    paraformer_counts = paraformer["full_audio"]["occurrence_reviewed_counts"]
    require_equal(
        "Paraformer-zh surface recovery",
        {
            "recovered": paraformer_counts["exact_surface_correct_recovery"],
            "denominator": paraformer["full_audio"][
                "previously_labeled_confirmed_masked_rows"
            ],
        },
        {"recovered": 2, "denominator": 97},
    )

    blind_rows = load_csv(
        "results/paper_tables/paper_assets_20260608/"
        "targeted_audit_110_blind_relabel_30_agreement_20260620.csv"
    )
    full_matches = sum(row["match"].strip().lower() == "true" for row in blind_rows)
    masked_matches = sum(
        (row["original_label"].strip() == "confirmed masked")
        == (row["blind_label"].strip() == "confirmed masked")
        for row in blind_rows
    )
    masked_kappa = binary_kappa(
        [row["original_label"].strip() == "confirmed masked" for row in blind_rows],
        [row["blind_label"].strip() == "confirmed masked" for row in blind_rows],
    )
    require_equal(
        "independent blind relabel agreement",
        {
            "full_labels": f"{full_matches}/{len(blind_rows)}",
            "masked_vs_other": f"{masked_matches}/{len(blind_rows)}",
            "masked_vs_other_kappa": rounded(masked_kappa),
        },
        {
            "full_labels": "23/30",
            "masked_vs_other": "27/30",
            "masked_vs_other_kappa": 0.8,
        },
    )

    human = load_json(
        "labels/human_200/human_review_200_official_summary_20260606.json"
    )["official_clamped_primary_overall"]
    require_equal(
        "200-case human case-macro accuracy",
        {
            "raw": rounded(human["raw_mean"]),
            "structured": rounded(human["structured_mean"]),
            "delta": rounded(human["delta"]),
        },
        {"raw": 0.8889, "structured": 0.9503, "delta": 0.0614},
    )

    runpy.run_path(str(ROOT / "scripts/verify_clip_revision.py"), run_name="__main__")
    print("Original audit records and current corrected clip claims verified.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, OSError, ValueError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        raise SystemExit(1)
