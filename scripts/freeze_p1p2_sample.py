#!/usr/bin/env python3
"""Freeze the shared P1/P2 200-case sample.

The frozen sample is the join point for:
- P1 human review expansion and IAA design.
- P2 API/GPU experiment matrix.

Selection policy:
- Keep all 50 cases from the current 4-pipeline MVP for continuity.
- Target 200 total cases:
  - 85 cdrd_entity
  - 35 cdrd_polyphone
  - 80 non_cdrd
- Prefer real news cases. The real_500 pool only has 35 non_cdrd cases, so
  synthetic non_cdrd cases fill the remaining non_cdrd quota.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


ROOT = Path("PROJECT_ROOT_PLACEHOLDER")
OUT_DIR = ROOT / "mvp_eval" / "p1p2"
REAL_500 = ROOT / "mvp_data" / "cn_newstts_real_500_candidates.xlsx"
SYNTH_5K = ROOT / "mvp_data" / "cn_newstts_synth_5k.jsonl"
SEED_EVAL = ROOT / "mvp_eval" / "eval_50_input.with_polynorm.xlsx"
MAPPING = ROOT / "cdrd_mapping.yaml"

FROZEN_XLSX = OUT_DIR / "p1p2_frozen_200_cases.xlsx"
FROZEN_CSV = OUT_DIR / "p1p2_frozen_200_cases.csv"
FROZEN_JSONL = OUT_DIR / "p1p2_frozen_200_cases.jsonl"
EVAL_RS_XLSX = OUT_DIR / "p1p2_eval_200_raw_structured.xlsx"
EVAL_RS_JSONL = OUT_DIR / "p1p2_eval_200_raw_structured.jsonl"
MANIFEST = OUT_DIR / "p1p2_freeze_manifest.json"

TARGET_COUNTS = {
    "cdrd_entity": 85,
    "cdrd_polyphone": 35,
    "non_cdrd": 80,
}

CDRD_FOCUS_TYPES = {
    "sports_score_hyphen",
    "sports_score_colon",
    "military_model_hyphen",
    "range_hyphen",
    "year_range_hyphen",
    "quarter_finance",
    "quarter_product",
    "generation_label",
    "vehicle_model_number",
}


def load_mapping() -> tuple[dict[str, str], list[str]]:
    data = yaml.safe_load(MAPPING.read_text(encoding="utf-8"))
    return data["mapping"], data["case_label_priority"]


TYPE_TO_CLASS, PRIORITY = load_mapping()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_json(value: Any, default: Any) -> Any:
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except Exception:
            return default
    if isinstance(value, (list, dict)):
        return value
    return default


def json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def case_label(span_types: list[str]) -> str:
    classes = {
        TYPE_TO_CLASS.get(t)
        for t in span_types
        if TYPE_TO_CLASS.get(t) and TYPE_TO_CLASS.get(t) != "not_applicable"
    }
    for label in PRIORITY:
        if label in classes:
            return label
    return "no_risk"


def risk_types(spans: list[dict[str, Any]]) -> list[str]:
    return sorted({str(s.get("type")) for s in spans if isinstance(s, dict) and s.get("type")})


def raw_text_from_parts(title: str, summary: str) -> str:
    title = str(title or "").strip()
    summary = str(summary or "").strip()
    if title and summary:
        return f"{title}。{summary}"
    return title or summary


def normalize_real_rows() -> list[dict[str, Any]]:
    df = pd.read_excel(REAL_500)
    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        spans = parse_json(r.get("risk_spans_json"), [])
        types = risk_types(spans)
        rows.append({
            "case_id": str(r["id"]),
            "source": "real_news",
            "domain": str(r.get("domain") or "general"),
            "raw_title": str(r.get("raw_title") or ""),
            "raw_summary": str(r.get("raw_summary") or ""),
            "raw_text": raw_text_from_parts(r.get("raw_title"), r.get("raw_summary")),
            "structured_text": str(r.get("spoken_text") or ""),
            "pronunciation_dict_json": str(r.get("pronunciation_dict_json") or '{"tone":[]}'),
            "risk_spans_json": json_dumps(spans),
            "risk_types": ";".join(types),
            "risk_span_count": len(spans),
            "cdrd_label": case_label(types),
            "review_status": str(r.get("review_status") or ""),
            "reviewer_note": "" if pd.isna(r.get("reviewer_note")) else str(r.get("reviewer_note")),
        })
    return rows


def normalize_synth_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with SYNTH_5K.open(encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            spans = obj.get("risk_spans") or []
            types = risk_types(spans)
            rows.append({
                "case_id": str(obj["id"]),
                "source": "synthetic",
                "domain": str(obj.get("domain") or "general"),
                "raw_title": str(obj.get("raw_title") or ""),
                "raw_summary": str(obj.get("raw_summary") or ""),
                "raw_text": str(obj.get("raw_text") or raw_text_from_parts(obj.get("raw_title"), obj.get("raw_summary"))),
                "structured_text": str(obj.get("spoken_text") or ""),
                "pronunciation_dict_json": json_dumps(obj.get("pronunciation_dict") or {"tone": []}),
                "risk_spans_json": json_dumps(spans),
                "risk_types": ";".join(types),
                "risk_span_count": len(spans),
                "cdrd_label": case_label(types),
                "review_status": str((obj.get("metadata") or {}).get("review_status") or ""),
                "reviewer_note": "",
            })
    return rows


def seed_case_ids() -> set[str]:
    if not SEED_EVAL.exists():
        return set()
    df = pd.read_excel(SEED_EVAL)
    return set(df[df["pipeline"].eq("raw")]["case_id"].astype(str))


def candidate_score(row: dict[str, Any], selected_type_counts: Counter, selected_domain_counts: Counter) -> tuple:
    types = row["risk_types"].split(";") if row["risk_types"] else []
    focus_hits = sum(1 for t in types if t in CDRD_FOCUS_TYPES)
    rare_bonus = sum(1.0 / (1 + selected_type_counts[t]) for t in types)
    domain_bonus = 1.0 / (1 + selected_domain_counts[row["domain"]])
    source_bonus = 1 if row["source"] == "real_news" else 0
    return (
        source_bonus,
        focus_hits,
        round(rare_bonus, 6),
        round(domain_bonus, 6),
        row["risk_span_count"],
        row["case_id"],
    )


def select_rows(all_rows: list[dict[str, Any]], seeds: set[str]) -> list[dict[str, Any]]:
    by_id = {r["case_id"]: r for r in all_rows}
    selected: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    label_counts: Counter = Counter()
    type_counts: Counter = Counter()
    domain_counts: Counter = Counter()

    for cid in sorted(seeds):
        row = by_id.get(cid)
        if not row:
            continue
        selected.append({**row, "selection_reason": "seed_eval_50"})
        selected_ids.add(cid)
        label_counts[row["cdrd_label"]] += 1
        domain_counts[row["domain"]] += 1
        type_counts.update(row["risk_types"].split(";") if row["risk_types"] else [])

    def fill_label(label: str) -> None:
        nonlocal selected, selected_ids
        while label_counts[label] < TARGET_COUNTS[label]:
            candidates = [
                r for r in all_rows
                if r["case_id"] not in selected_ids and r["cdrd_label"] == label
            ]
            if not candidates:
                raise RuntimeError(f"Not enough candidates for {label}: have {label_counts[label]}, target {TARGET_COUNTS[label]}")
            # For non_cdrd, exhaust real cases before synthetic, then use synthetic.
            candidates.sort(
                key=lambda r: candidate_score(r, type_counts, domain_counts),
                reverse=True,
            )
            row = candidates[0]
            selected.append({**row, "selection_reason": f"fill_{label}"})
            selected_ids.add(row["case_id"])
            label_counts[label] += 1
            domain_counts[row["domain"]] += 1
            type_counts.update(row["risk_types"].split(";") if row["risk_types"] else [])

    for label in ("cdrd_entity", "cdrd_polyphone", "non_cdrd"):
        fill_label(label)

    if len(selected) != sum(TARGET_COUNTS.values()):
        raise RuntimeError(f"Expected {sum(TARGET_COUNTS.values())} selected, got {len(selected)}")
    return selected


def write_eval_inputs(frozen_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in frozen_df.iterrows():
        common = {
            "case_id": r["case_id"],
            "source": r["source"],
            "cdrd_label": r["cdrd_label"],
            "domain": r["domain"],
            "raw_text": r["raw_text"],
            "pronunciation_dict_json": r["pronunciation_dict_json"],
            "risk_spans_json": r["risk_spans_json"],
        }
        rows.append({
            **common,
            "pipeline": "raw",
            "tts_input_text": r["raw_text"],
        })
        rows.append({
            **common,
            "pipeline": "structured",
            "tts_input_text": r["structured_text"],
        })
    out = pd.DataFrame(rows)
    cols = [
        "case_id", "source", "cdrd_label", "pipeline", "domain",
        "raw_text", "tts_input_text", "pronunciation_dict_json", "risk_spans_json",
    ]
    out = out[cols]
    out.to_excel(EVAL_RS_XLSX, index=False)
    with EVAL_RS_JSONL.open("w", encoding="utf-8") as f:
        for row in out.to_dict("records"):
            f.write(json_dumps(row) + "\n")
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    real_rows = normalize_real_rows()
    synth_rows = normalize_synth_rows()
    seeds = seed_case_ids()
    selected = select_rows(real_rows + synth_rows, seeds)

    frozen = pd.DataFrame(selected)
    frozen = frozen.sort_values(["cdrd_label", "source", "case_id"]).reset_index(drop=True)
    frozen.insert(0, "freeze_id", [f"P1P2_{i:03d}" for i in range(1, len(frozen) + 1)])
    frozen.to_excel(FROZEN_XLSX, index=False)
    frozen.to_csv(FROZEN_CSV, index=False)
    with FROZEN_JSONL.open("w", encoding="utf-8") as f:
        for row in frozen.to_dict("records"):
            f.write(json_dumps(row) + "\n")

    eval_df = write_eval_inputs(frozen)

    manifest = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target_counts": TARGET_COUNTS,
        "selected_rows": int(len(frozen)),
        "eval_rows_raw_structured": int(len(eval_df)),
        "counts": {
            "cdrd_label": frozen["cdrd_label"].value_counts().to_dict(),
            "source": frozen["source"].value_counts().to_dict(),
            "domain": frozen["domain"].value_counts().to_dict(),
            "selection_reason": frozen["selection_reason"].value_counts().to_dict(),
        },
        "input_hashes": {
            str(REAL_500.relative_to(ROOT)): sha256(REAL_500),
            str(SYNTH_5K.relative_to(ROOT)): sha256(SYNTH_5K),
            str(SEED_EVAL.relative_to(ROOT)): sha256(SEED_EVAL) if SEED_EVAL.exists() else None,
            str(MAPPING.relative_to(ROOT)): sha256(MAPPING),
        },
        "outputs": {
            "frozen_xlsx": str(FROZEN_XLSX.relative_to(ROOT)),
            "frozen_csv": str(FROZEN_CSV.relative_to(ROOT)),
            "frozen_jsonl": str(FROZEN_JSONL.relative_to(ROOT)),
            "eval_raw_structured_xlsx": str(EVAL_RS_XLSX.relative_to(ROOT)),
            "eval_raw_structured_jsonl": str(EVAL_RS_JSONL.relative_to(ROOT)),
        },
        "note": "This sample freezes case IDs only. Do not change structured v5.1 rules for this experimental round.",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "frozen_cases": len(frozen),
        "eval_rows_raw_structured": len(eval_df),
        "counts": manifest["counts"],
        "out_dir": str(OUT_DIR),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
