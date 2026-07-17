#!/usr/bin/env python3
"""Review aligned span-isolated ASR probe outputs.

This script adds a conservative manual-review layer on top of the automatic
string matcher used by run_span_isolated_asr_probe_20260612.py.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROBE_DIR = ROOT / "mvp_eval" / "span_isolated_asr_probe_20260612"
ALIGNED_RESULTS = PROBE_DIR / "outputs" / "mimo_strict_aligned_whisper_ts_results.jsonl"
ROUGH_REVIEWED = PROBE_DIR / "outputs" / "mimo_strict_span_iso_6s_results.reviewed.jsonl"
ALIGNED_REVIEWED_JSONL = (
    PROBE_DIR / "outputs" / "mimo_strict_aligned_whisper_ts_results.reviewed.jsonl"
)
ALIGNED_REVIEWED_CSV = (
    PROBE_DIR / "outputs" / "mimo_strict_aligned_whisper_ts_results.reviewed.csv"
)
SUMMARY_MD = (
    PROBE_DIR / "span_isolated_asr_probe_reviewed_summary_aligned_whisper_ts_20260612.md"
)
TABLE_MD = PROBE_DIR / "table_full_vs_rough_vs_aligned_asr_probe_20260612.md"
ALIGN_MANIFEST = (
    PROBE_DIR
    / "aligned_whisper_ts"
    / "aligned_manifest_whisper_ts_46.local.jsonl"
)


# Labels:
# - exposed: isolated ASR surfaces the erroneous/non-canonical reading.
# - still_masked: isolated ASR returns the expected/canonical reading.
# - no_output: no usable isolated ASR output.
# - other_transcript: output is usable text but does not judge the target reading.
REVIEW = {
    "PCP2_0001": ("no_output", "empty isolated ASR output"),
    "PCP2_0003": ("exposed", "outputs 六之二, a close homophone of 六至二 rather than 六比二"),
    "PCP2_0004": ("no_output", "empty isolated ASR output"),
    "PCP2_0005": ("still_masked", "outputs 十三比九"),
    "PCP2_0007": ("no_output", "empty isolated ASR output"),
    "PCP2_0008": ("other_transcript", "no clear target reading; transcript drifts to 实至时候"),
    "PCP2_0009": ("still_masked", "outputs 六比三"),
    "PCP2_0011": ("exposed", "outputs 三至六"),
    "PCP2_0014": ("still_masked", "outputs 十一比七"),
    "PCP2_0015": ("still_masked", "outputs 二比一"),
    "PCP2_0017": ("still_masked", "outputs 四比三"),
    "PCP2_0018": ("exposed", "outputs 十一至七"),
    "PCP2_0019": ("exposed", "outputs 二之一, a non-score reading close to 二至一"),
    "PCP2_0020": ("exposed", "outputs 四至三"),
    "PCP2_0021": ("exposed", "outputs 二十一至十七"),
    "PCP2_0023": ("no_output", "empty isolated ASR output"),
    "PCP2_0024": ("no_output", "empty isolated ASR output"),
    "PCP2_0026": ("exposed", "outputs 零至三"),
    "PCP2_0027": ("no_output", "empty isolated ASR output"),
    "PCP2_0028": ("exposed", "outputs 三至零"),
    "PCP2_0029": ("exposed", "outputs F杠三五"),
    "PCP2_0030": ("no_output", "empty isolated ASR output"),
    "PCP2_0031": ("no_output", "empty isolated ASR output"),
    "PCP2_0032": ("still_masked", "outputs F-35"),
    "PCP2_0033": ("exposed", "outputs 运辅二十B, exposing fu/二十 instead of 运二零B"),
    "PCP2_0034": ("exposed", "outputs B杠二"),
    "PCP2_0035": ("still_masked", "outputs F-18"),
    "PCP2_0036": ("exposed", "outputs 伊尔负七十六"),
    "PCP2_0037": ("exposed", "outputs F杠十六"),
    "PCP2_0043": ("no_output", "empty isolated ASR output"),
    "PCP2_0056": ("other_transcript", "does not clearly recover 190N·M or 190牛·米"),
    "PCP2_0062": ("exposed", "outputs 七百五十兆W"),
    "PCP2_0064": (
        "still_masked",
        "outputs accepted aircraft-model variant 七三七杠八 rather than the human-heard 七三七负八",
    ),
    "PCP2_0079": ("no_output", "empty isolated ASR output"),
    "PCP2_0081": ("still_masked", "outputs 一百零五千瓦"),
    "PCP2_0082": ("still_masked", "outputs 二百千瓦"),
    "PCP2_0083": ("still_masked", "outputs 二百三十千瓦"),
    "PCP2_0084": ("no_output", "empty isolated ASR output"),
    "PCP2_0085": ("exposed", "outputs 十五KW"),
    "PCP2_0087": ("no_output", "empty isolated ASR output"),
    "PCP2_0090": ("no_output", "empty isolated ASR output"),
    "PCP2_0092": ("exposed", "partial unit-letter exposure: outputs 五百K, not 五百千瓦"),
    "PCP2_0093": ("exposed", "partial unit-letter exposure: outputs 五百K D, not 五百千瓦"),
    "PCP2_0094": ("other_transcript", "does not clearly recover 八十八伏IP or 八十八VIP"),
    "PCP2_0102": ("still_masked", "outputs 三百五十瓦时每公斤"),
    "PCP2_0110": ("exposed", "outputs 六G W"),
}


STRONG_EXPOSED_EXCLUDE = {"PCP2_0092", "PCP2_0093"}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def pct(n: int, d: int) -> str:
    return f"{n / d * 100:.1f}%" if d else "0.0%"


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict]) -> None:
    columns = [
        "probe_candidate_id",
        "case_id",
        "freeze_id",
        "primary_type",
        "target_span",
        "expected_reading",
        "raw_tts_actual_reading",
        "isolated_asr_text",
        "isolated_asr_label",
        "reviewed_isolated_asr_label",
        "reviewed_exposure_strength",
        "reviewed_label_note",
        "alignment_method",
        "alignment_candidate",
        "aligned_clip_start_seconds",
        "aligned_clip_end_seconds",
        "aligned_clip_duration_seconds",
        "clip_audio_path",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def count_labels(rows: list[dict], key: str) -> Counter:
    return Counter(row.get(key, "") for row in rows)


def make_count_table(title: str, counts: Counter, total: int) -> str:
    order = ["exposed", "still_masked", "no_output", "other_transcript"]
    lines = [f"### {title}", "", "| label | count | percent |", "|---|---:|---:|"]
    for label in order:
        n = counts.get(label, 0)
        lines.append(f"| {label} | {n} | {pct(n, total)} |")
    return "\n".join(lines)


def main() -> None:
    rows = load_jsonl(ALIGNED_RESULTS)
    if len(rows) != len(REVIEW):
        raise SystemExit(f"review map size mismatch: rows={len(rows)} review={len(REVIEW)}")

    missing = sorted({row["probe_candidate_id"] for row in rows} ^ set(REVIEW))
    if missing:
        raise SystemExit(f"review id mismatch: {missing}")

    reviewed_rows = []
    for row in rows:
        label, note = REVIEW[row["probe_candidate_id"]]
        out = dict(row)
        out["reviewed_isolated_asr_label"] = label
        out["reviewed_label_note"] = note
        if label == "exposed":
            out["reviewed_exposure_strength"] = (
                "partial" if row["probe_candidate_id"] in STRONG_EXPOSED_EXCLUDE else "strong"
            )
        else:
            out["reviewed_exposure_strength"] = ""
        reviewed_rows.append(out)

    write_jsonl(ALIGNED_REVIEWED_JSONL, reviewed_rows)
    write_csv(ALIGNED_REVIEWED_CSV, reviewed_rows)

    rough_rows = load_jsonl(ROUGH_REVIEWED)
    align_rows = load_jsonl(ALIGN_MANIFEST)
    total = len(reviewed_rows)
    full_counts = Counter({"still_masked": total})
    rough_counts = count_labels(rough_rows, "reviewed_isolated_asr_label")
    aligned_machine_counts = count_labels(rows, "isolated_asr_label")
    aligned_reviewed_counts = count_labels(reviewed_rows, "reviewed_isolated_asr_label")
    align_method_counts = Counter(row.get("alignment_method", "") for row in align_rows)
    strong_exposed = sum(
        1
        for row in reviewed_rows
        if row["reviewed_isolated_asr_label"] == "exposed"
        and row["reviewed_exposure_strength"] == "strong"
    )
    partial_exposed = sum(
        1 for row in reviewed_rows if row.get("reviewed_exposure_strength") == "partial"
    )

    summary = [
        "# Span-Isolated ASR Probe, Aligned Review (2026-06-12)",
        "",
        "## Scope",
        "",
        "- Pool: 46 prior MiMo `confirmed masked` cases.",
        "- Alignment: Whisper-small word/chunk timestamps on the workstation, then aligned clips were transcribed by MiMo strict ASR.",
        "- Control: each full sentence was masked by at least one case-specific ASR route; all isolated clips use MiMo strict ASR.",
        "",
        "## Alignment",
        "",
        "| alignment method | count | percent |",
        "|---|---:|---:|",
    ]
    for method, n in align_method_counts.most_common():
        summary.append(f"| {method} | {n} | {pct(n, total)} |")
    summary.extend(
        [
            "",
            "## Reviewed Outcome",
            "",
            make_count_table("Full-sentence ASR baseline", full_counts, total),
            "",
            make_count_table("Rough 6s span-isolated clips", rough_counts, total),
            "",
            make_count_table("Aligned span-isolated clips, machine labels", aligned_machine_counts, total),
            "",
            make_count_table("Aligned span-isolated clips, reviewed labels", aligned_reviewed_counts, total),
            "",
            "## Exposure Strength",
            "",
            f"- Strong exposed cases: {strong_exposed}/{total} ({pct(strong_exposed, total)}).",
            f"- Partial unit-letter exposed cases: {partial_exposed}/{total} ({pct(partial_exposed, total)}).",
            f"- Total reviewed exposed cases including partial: {aligned_reviewed_counts['exposed']}/{total} ({pct(aligned_reviewed_counts['exposed'], total)}).",
            "",
            "## Interpretation",
            "",
            "Aligned slicing reduces no-output cases compared with the rough 6s heuristic and surfaces more wrong-reading evidence.",
            "The transition is consistent with a contextual contribution to masking, but the full-context masking route is case-specific whereas all isolated clips use MiMo strict ASR.",
            "This is therefore a cross-route mechanism probe, not a protocol-matched accuracy metric; some aligned clips are also too short or acoustically ambiguous.",
            "",
            "Recommended next step: rerun the aligned clips with a slightly wider minimum window/padding, or move to forced-choice acoustic scoring for expected vs. negative readings.",
            "",
            "## Outputs",
            "",
            "- Reviewed JSONL: `outputs/mimo_strict_aligned_whisper_ts_results.reviewed.jsonl`",
            "- Reviewed CSV: `outputs/mimo_strict_aligned_whisper_ts_results.reviewed.csv`",
            "- Aligned clips: `aligned_whisper_ts/clips/`",
        ]
    )
    SUMMARY_MD.write_text("\n".join(summary) + "\n", encoding="utf-8")

    labels = ["exposed", "still_masked", "no_output", "other_transcript"]
    table = [
        "# Full vs Rough vs Aligned Span-Isolated ASR Probe",
        "",
        "| setting | exposed | still_masked | no_output | other_transcript | note |",
        "|---|---:|---:|---:|---:|---|",
        "| Full sentence, original audit route | "
        + " | ".join(str(full_counts.get(label, 0)) for label in labels)
        + " | Case-specific full-context route; all 46 masked by construction |",
        "| Rough 6s span-isolated ASR | "
        + " | ".join(str(rough_counts.get(label, 0)) for label in labels)
        + " | Text-ratio approximate window |",
        "| Aligned span-isolated ASR, machine | "
        + " | ".join(str(aligned_machine_counts.get(label, 0)) for label in labels)
        + " | Direct string matcher before review |",
        "| Aligned span-isolated ASR, reviewed | "
        + " | ".join(str(aligned_reviewed_counts.get(label, 0)) for label in labels)
        + f" | Strong exposed={strong_exposed}; partial unit-letter exposed={partial_exposed} |",
        "",
    ]
    TABLE_MD.write_text("\n".join(table), encoding="utf-8")

    print(f"reviewed_jsonl={ALIGNED_REVIEWED_JSONL}")
    print(f"reviewed_csv={ALIGNED_REVIEWED_CSV}")
    print(f"summary_md={SUMMARY_MD}")
    print(f"table_md={TABLE_MD}")
    print("aligned reviewed counts", dict(aligned_reviewed_counts))
    print("strong_exposed", strong_exposed, "partial_exposed", partial_exposed)


if __name__ == "__main__":
    main()
