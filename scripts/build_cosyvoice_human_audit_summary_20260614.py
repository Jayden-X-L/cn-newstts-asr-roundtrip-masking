#!/usr/bin/env python3
"""Import and summarize CosyVoice Raw-110 human review labels."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_JSON = Path(
    "ANNOTATION_EXPORT_DIR_PLACEHOLDER/cosyvoice_raw_110_human_review_labels_20260608 .json"
)
OUT_DIR = ROOT / "mvp_eval" / "cosyvoice_targeted_20260608" / "human_labels_20260614"
RAW_COPY = OUT_DIR / "cosyvoice_raw_110_human_review_labels_raw_export_20260614.json"
FINAL_JSONL = OUT_DIR / "cosyvoice_raw_110_human_review_labels_final_20260614.jsonl"
FINAL_CSV = OUT_DIR / "cosyvoice_raw_110_human_review_labels_final_20260614.csv"
SUMMARY_MD = OUT_DIR / "cosyvoice_raw_110_human_review_summary_20260614.md"
TABLE_MD = OUT_DIR / "table_cosyvoice_raw_110_human_review_yield_20260614.md"


OUTCOME_ORDER = [
    "confirmed masked",
    "exposed TTS error",
    "no Raw TTS error",
    "uncertain",
    "not judgeable",
]


def pct(n: int, d: int) -> str:
    return f"{n / d * 100:.1f}%" if d else "0.0%"


def load_rows() -> list[dict]:
    rows = json.loads(SOURCE_JSON.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise TypeError(f"Expected list in {SOURCE_JSON}")
    return rows


def normalize_rows(rows: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for row in rows:
        out = dict(row)
        out["normalization_note"] = ""
        # The reviewer outcome and evidence note indicate masking by MiMo ASR:
        # ASR text contains "二百牛米"; only the behavior dropdown was inconsistent.
        if out.get("probe_candidate_id") == "PCP2_0081":
            out["mimo_asr_behavior_original"] = out.get("mimo_asr_behavior", "")
            out["mimo_asr_behavior"] = "writes expected/correct"
            out["normalization_note"] = (
                "Corrected inconsistent behavior dropdown: evidence_note and MiMo ASR text "
                "show 二百牛米, so MiMo ASR masks the CosyVoice reading 二百nm."
            )
        normalized.append(out)
    return normalized


def counter_table(title: str, counts: Counter, total: int, order: list[str] | None = None) -> str:
    labels = order or [k for k, _ in counts.most_common()]
    lines = [f"### {title}", "", "| category | count | share |", "|---|---:|---:|"]
    for label in labels:
        n = counts.get(label, 0)
        lines.append(f"| {label or '(blank)'} | {n} | {pct(n, total)} |")
    return "\n".join(lines)


def write_outputs(rows: list[dict], normalized: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RAW_COPY.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with FINAL_JSONL.open("w", encoding="utf-8") as f:
        for row in normalized:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    columns = [
        "probe_candidate_id",
        "case_id",
        "freeze_id",
        "source",
        "domain",
        "cdrd_label",
        "primary_type",
        "prior_mimo_audit_outcome",
        "cosyvoice_outcome",
        "confidence",
        "target_span_review",
        "expected_reading_review",
        "cosyvoice_heard_reading",
        "mimo_asr_behavior",
        "whisper_asr_behavior",
        "evidence_note",
        "reviewer_note",
        "normalization_note",
        "audio_path",
        "exported_at",
    ]
    with FINAL_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(normalized)


def build_summary(rows: list[dict], normalized: list[dict]) -> None:
    total = len(normalized)
    outcome_counts = Counter(row.get("cosyvoice_outcome", "") for row in normalized)
    confidence_counts = Counter(row.get("confidence", "") for row in normalized)
    type_counts: dict[str, Counter] = defaultdict(Counter)
    cdrd_counts: dict[str, Counter] = defaultdict(Counter)
    for row in normalized:
        type_counts[row.get("primary_type", "")][row.get("cosyvoice_outcome", "")] += 1
        cdrd_counts[row.get("cdrd_label", "")][row.get("cosyvoice_outcome", "")] += 1

    confirmed = [row for row in normalized if row.get("cosyvoice_outcome") == "confirmed masked"]
    exposed = [row for row in normalized if row.get("cosyvoice_outcome") == "exposed TTS error"]
    no_error = [row for row in normalized if row.get("cosyvoice_outcome") == "no Raw TTS error"]
    uncertain = [row for row in normalized if row.get("cosyvoice_outcome") == "uncertain"]
    not_judgeable = [row for row in normalized if row.get("cosyvoice_outcome") == "not judgeable"]

    confirmed_pair_counts = Counter(
        (row.get("mimo_asr_behavior", ""), row.get("whisper_asr_behavior", ""))
        for row in confirmed
    )
    confirmed_mimo_masked = sum(
        1 for row in confirmed if row.get("mimo_asr_behavior") == "writes expected/correct"
    )
    confirmed_whisper_masked = sum(
        1 for row in confirmed if row.get("whisper_asr_behavior") == "writes expected/correct"
    )
    confirmed_both_masked = sum(
        1
        for row in confirmed
        if row.get("mimo_asr_behavior") == "writes expected/correct"
        and row.get("whisper_asr_behavior") == "writes expected/correct"
    )
    confirmed_either_masked = sum(
        1
        for row in confirmed
        if row.get("mimo_asr_behavior") == "writes expected/correct"
        or row.get("whisper_asr_behavior") == "writes expected/correct"
    )

    table_lines = [
        "# CosyVoice Raw-110 Human Review Yield (2026-06-14)",
        "",
        "| Category | Count | Share | Meaning |",
        "|---|---:|---:|---|",
        f"| confirmed masked | {len(confirmed)} | {pct(len(confirmed), total)} | CosyVoice Raw TTS is wrong and at least one ASR route writes the expected/surface-correct form |",
        f"| exposed TTS error | {len(exposed)} | {pct(len(exposed), total)} | CosyVoice Raw TTS is wrong and the error is exposed rather than masked in review |",
        f"| no Raw TTS error | {len(no_error)} | {pct(len(no_error), total)} | CosyVoice Raw audio is judged correct for the audited span |",
        f"| uncertain | {len(uncertain)} | {pct(len(uncertain), total)} | Evidence insufficient |",
        f"| not judgeable | {len(not_judgeable)} | {pct(len(not_judgeable), total)} | Audio/span/gold/metadata unsuitable |",
        f"| total targeted pool | {total} | 100.0% | Same 110 high-risk audit pool, Raw-only CosyVoice |",
        "",
    ]
    TABLE_MD.write_text("\n".join(table_lines), encoding="utf-8")

    summary = [
        "# CosyVoice Raw-110 Human Review Summary (2026-06-14)",
        "",
        "## Scope",
        "",
        "- TTS: CosyVoice-300M-SFT, Raw input only.",
        "- Pool: same 110 targeted high-risk rows used for the MiMo masked-error audit.",
        "- ASR evidence: MiMo strict ASR and Whisper-small ASR transcripts are shown in the review page.",
        "- Human label source: `ANNOTATION_EXPORT_DIR_PLACEHOLDER/cosyvoice_raw_110_human_review_labels_20260608 .json`.",
        "- Outcome definition for `confirmed masked`: CosyVoice Raw TTS is wrong and at least one ASR route writes the expected/surface-correct form.",
        "",
        "## Yield",
        "",
        counter_table("Overall outcome", outcome_counts, total, OUTCOME_ORDER),
        "",
        "## ASR-Route Split within Confirmed Masked",
        "",
        "| ASR masking route | Count | Share of confirmed masked |",
        "|---|---:|---:|",
        f"| MiMo strict ASR writes expected/correct | {confirmed_mimo_masked} | {pct(confirmed_mimo_masked, len(confirmed))} |",
        f"| Whisper-small ASR writes expected/correct | {confirmed_whisper_masked} | {pct(confirmed_whisper_masked, len(confirmed))} |",
        f"| Both ASR routes write expected/correct | {confirmed_both_masked} | {pct(confirmed_both_masked, len(confirmed))} |",
        f"| At least one ASR route writes expected/correct | {confirmed_either_masked} | {pct(confirmed_either_masked, len(confirmed))} |",
        "",
        "Pair counts within confirmed masked:",
        "",
        "| MiMo strict ASR behavior | Whisper-small ASR behavior | Count |",
        "|---|---|---:|",
    ]
    for (mimo, whisper), n in confirmed_pair_counts.most_common():
        summary.append(f"| {mimo or '(blank)'} | {whisper or '(blank)'} | {n} |")

    summary.extend(["", "## By Primary Type", "", "| primary_type | confirmed masked | exposed TTS error | no Raw TTS error | uncertain | not judgeable | total |", "|---|---:|---:|---:|---:|---:|---:|"])
    for typ in sorted(type_counts):
        c = type_counts[typ]
        row_total = sum(c.values())
        summary.append(
            f"| {typ} | {c.get('confirmed masked', 0)} | {c.get('exposed TTS error', 0)} | "
            f"{c.get('no Raw TTS error', 0)} | {c.get('uncertain', 0)} | {c.get('not judgeable', 0)} | {row_total} |"
        )

    summary.extend(["", "## By CDRD Label", "", "| cdrd_label | confirmed masked | exposed TTS error | no Raw TTS error | uncertain | not judgeable | total |", "|---|---:|---:|---:|---:|---:|---:|"])
    for label in sorted(cdrd_counts):
        c = cdrd_counts[label]
        row_total = sum(c.values())
        summary.append(
            f"| {label} | {c.get('confirmed masked', 0)} | {c.get('exposed TTS error', 0)} | "
            f"{c.get('no Raw TTS error', 0)} | {c.get('uncertain', 0)} | {c.get('not judgeable', 0)} | {row_total} |"
        )

    summary.extend(
        [
            "",
            "## Consistency Notes",
            "",
            "- Original human-review JSON is preserved unchanged.",
            "- Final normalized table corrects one inconsistent dropdown on `PCP2_0081`: the outcome and evidence note indicate MiMo ASR wrote the expected `二百牛米`, so `mimo_asr_behavior` is normalized from `exposes wrong reading` to `writes expected/correct` with `normalization_note` populated.",
            "- `confidence` is only filled for high-confidence positive/ambiguous rows in the exported review UI; blank confidence should not be read as low confidence for `no Raw TTS error` rows.",
            "",
            "## Interpretation",
            "",
            "The completed human review upgrades the second-TTS targeted run from a pending package to confirmed external validation evidence.",
            "CosyVoice reproduces the same broad phenomenon: in the same high-risk pool, Raw-only synthesis contains listener-facing reading errors, and ASR can write at least some of those errors back to an expected or surface-correct transcript.",
            "Because the pool is targeted and hard-case enriched, the 51/110 yield should not be interpreted as production prevalence.",
            "",
            "## Outputs",
            "",
            f"- Raw JSON copy: `{RAW_COPY}`",
            f"- Final JSONL: `{FINAL_JSONL}`",
            f"- Final CSV: `{FINAL_CSV}`",
            f"- Paper table: `{TABLE_MD}`",
        ]
    )
    SUMMARY_MD.write_text("\n".join(summary) + "\n", encoding="utf-8")


def main() -> None:
    rows = load_rows()
    normalized = normalize_rows(rows)
    write_outputs(rows, normalized)
    build_summary(rows, normalized)
    counts = Counter(row.get("cosyvoice_outcome", "") for row in normalized)
    print(f"rows={len(normalized)}")
    print(dict(counts))
    print(f"summary={SUMMARY_MD}")
    print(f"table={TABLE_MD}")


if __name__ == "__main__":
    main()
