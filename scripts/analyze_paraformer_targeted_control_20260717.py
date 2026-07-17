#!/usr/bin/env python3
"""Analyze Paraformer transcripts without treating ASR text as ground truth."""

from __future__ import annotations

import csv
import html
import json
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULT_DIR = ROOT / "mvp_eval/paraformer_targeted_20260717"
FULL_RESULTS = RESULT_DIR / "paraformer_full_220_results.jsonl"
ALIGNED_RESULTS = RESULT_DIR / "paraformer_aligned_46_results.jsonl"

SEPARATORS = set(" \t\r\n-‐‑‒–—:：·•/／_")

SURFACE_RECOVERY = "exact_surface_correct_recovery"
WRONG_PRESERVED = "wrong_or_noncanonical_form_preserved"
OTHER_NO_RECOVERY = "other_no_exact_surface_recovery"

# Full-transcript substring checks can conflate repeated spans.  These rows were
# reviewed occurrence by occurrence against the audited target position.
FULL_REVIEW_OVERRIDES = {
    "mimo_full_PCP2_0003": (WRONG_PRESERVED, "audited occurrence is 六之二; 六比二 occurs later"),
    "mimo_full_PCP2_0009": (WRONG_PRESERVED, "audited occurrence is 六至三"),
    "mimo_full_PCP2_0017": (WRONG_PRESERVED, "audited occurrence is 四至三; 四比三 occurs later"),
    "mimo_full_PCP2_0019": (WRONG_PRESERVED, "audited occurrence is 二至一; 二比一 is a later score"),
    "mimo_full_PCP2_0021": (WRONG_PRESERVED, "audited occurrence is 二十一至十七"),
    "mimo_full_PCP2_0023": (WRONG_PRESERVED, "audited occurrence is 六至二"),
    "mimo_full_PCP2_0028": (WRONG_PRESERVED, "audited occurrence is 三至零"),
    "mimo_full_PCP2_0031": (WRONG_PRESERVED, "audited occurrence retains 杠 in F杠幺五E"),
    "mimo_full_PCP2_0035": (WRONG_PRESERVED, "audited occurrence retains 杠 in F杠一八"),
    "mimo_full_PCP2_0036": (WRONG_PRESERVED, "audited occurrence is 伊尔夫七十六, a near-negative rendering"),
    "mimo_full_PCP2_0037": (WRONG_PRESERVED, "audited occurrence retains 杠 in F杠一六"),
    "mimo_full_PCP2_0056": (OTHER_NO_RECOVERY, "unit span is rendered as an unrelated non-surface phrase"),
    "mimo_full_PCP2_0090": (WRONG_PRESERVED, "audited occurrence retains the letters KW"),
    "mimo_full_PCP2_0094": (WRONG_PRESERVED, "audited occurrence remains a phonetic non-surface rendering"),
    "mimo_full_PCP2_0102": (OTHER_NO_RECOVERY, "unit span is rendered as an unrelated non-surface phrase"),
    "cosyvoice_full_PCP2_0017": (WRONG_PRESERVED, "audited occurrence is 四减三; 四比三 occurs later"),
    "cosyvoice_full_PCP2_0021": (WRONG_PRESERVED, "audited occurrence is 二十一减十七"),
    "cosyvoice_full_PCP2_0023": (WRONG_PRESERVED, "audited occurrence is 六减二"),
    "cosyvoice_full_PCP2_0030": (OTHER_NO_RECOVERY, "F十五E omits the negative marker but is not the annotated F一五E form"),
    "cosyvoice_full_PCP2_0031": (OTHER_NO_RECOVERY, "model span is garbled rather than exactly recovered"),
    "cosyvoice_full_PCP2_0034": (OTHER_NO_RECOVERY, "B-2 span contains an extra letter and is not exactly recovered"),
    "cosyvoice_full_PCP2_0035": (SURFACE_RECOVERY, "audited F-18 occurrence is transcribed exactly as F十八"),
    "cosyvoice_full_PCP2_0037": (SURFACE_RECOVERY, "audited F-16 occurrence is transcribed exactly as F十六"),
    "cosyvoice_full_PCP2_0055": (WRONG_PRESERVED, "audited range retains the negative marker"),
    "cosyvoice_full_PCP2_0056": (OTHER_NO_RECOVERY, "unit span remains a partial letter rendering"),
    "cosyvoice_full_PCP2_0065": (WRONG_PRESERVED, "audited year range retains the wrong first-year reading"),
    "cosyvoice_full_PCP2_0070": (WRONG_PRESERVED, "audited year range retains the wrong first-year reading"),
    "cosyvoice_full_PCP2_0075": (WRONG_PRESERVED, "audited range retains the negative marker"),
    "cosyvoice_full_PCP2_0077": (WRONG_PRESERVED, "audited occurrence is 三减零; 三比零 occurs later"),
    "cosyvoice_full_PCP2_0081": (WRONG_PRESERVED, "audited unit retains the letters NM"),
    "cosyvoice_full_PCP2_0088": (OTHER_NO_RECOVERY, "unit span is garbled rather than exactly recovered"),
}


def text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_for_match(value: Any) -> str:
    normalized = unicodedata.normalize("NFKC", text(value)).lower()
    return "".join(char for char in normalized if char not in SEPARATORS)


def load_latest(path: Path) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            latest[text(row.get("item_id"))] = row
    return list(latest.values())


def unique_forms(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    forms: list[str] = []
    for value in values:
        item = text(value)
        normalized = normalize_for_match(item)
        if item and normalized and normalized not in seen:
            seen.add(normalized)
            forms.append(item)
    return forms


def matching_forms(transcript: str, forms: list[str]) -> list[str]:
    normalized_transcript = normalize_for_match(transcript)
    return [form for form in forms if normalize_for_match(form) in normalized_transcript]


def score_row(row: dict[str, Any]) -> dict[str, Any]:
    transcript = text(row.get("asr_text"))
    surface_forms = unique_forms(
        [row.get("target_span"), row.get("expected_reading")]
    )
    surface_norms = {normalize_for_match(form) for form in surface_forms}
    negative_forms = [
        form
        for form in unique_forms(
            [row.get("human_heard_reading"), *(row.get("negative_readings") or [])]
        )
        if normalize_for_match(form) not in surface_norms
    ]
    surface_hits = matching_forms(transcript, surface_forms)
    negative_hits = matching_forms(transcript, negative_forms)

    if text(row.get("error")):
        relation = "asr_error"
    elif surface_hits and negative_hits:
        relation = "surface_and_negative"
    elif surface_hits:
        relation = "surface_correct_only"
    elif negative_hits:
        relation = "negative_only"
    else:
        relation = "no_predefined_form"

    return {
        **row,
        "surface_forms": surface_forms,
        "negative_forms_for_match": negative_forms,
        "surface_hits": surface_hits,
        "negative_hits": negative_hits,
        "automatic_asr_relation": relation,
        "requires_transcript_review": relation
        in {"surface_and_negative", "no_predefined_form", "asr_error"},
    }


def apply_occurrence_review(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ambiguous = {
        row["item_id"]
        for row in rows
        if row["automatic_asr_relation"] != "negative_only"
    }
    if ambiguous != set(FULL_REVIEW_OVERRIDES):
        missing = sorted(ambiguous - set(FULL_REVIEW_OVERRIDES))
        stale = sorted(set(FULL_REVIEW_OVERRIDES) - ambiguous)
        raise RuntimeError(f"review override mismatch; missing={missing}, stale={stale}")

    reviewed: list[dict[str, Any]] = []
    for row in rows:
        if row["automatic_asr_relation"] == "negative_only":
            relation = WRONG_PRESERVED
            note = "predefined negative reading occurs at the audited span"
        else:
            relation, note = FULL_REVIEW_OVERRIDES[row["item_id"]]
        reviewed.append(
            {
                **row,
                "reviewed_paraformer_relation": relation,
                "transcript_review_note": note,
            }
        )
    return reviewed


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = [
        "item_id",
        "audio_scope",
        "tts_system",
        "probe_candidate_id",
        "case_id",
        "human_audit_outcome",
        "cdrd_label",
        "primary_type",
        "target_span",
        "expected_reading",
        "human_heard_reading",
        "surface_hits",
        "negative_hits",
        "automatic_asr_relation",
        "requires_transcript_review",
        "reviewed_paraformer_relation",
        "transcript_review_note",
        "asr_text",
        "error",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            output = dict(row)
            for key in ("surface_hits", "negative_hits"):
                output[key] = " | ".join(row.get(key) or [])
            writer.writerow(output)


def relation_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(text(row["automatic_asr_relation"]) for row in rows))


def write_review_html(path: Path, rows: list[dict[str, Any]], title: str) -> None:
    cards: list[str] = []
    for row in rows:
        relation = text(row.get("automatic_asr_relation"))
        cards.append(
            f"""
<article data-relation="{html.escape(relation)}">
  <header><strong>{html.escape(text(row.get('item_id')))}</strong>
    <span>{html.escape(text(row.get('tts_system')))}</span>
    <span>{html.escape(relation)}</span></header>
  <dl>
    <dt>target</dt><dd>{html.escape(text(row.get('target_span')))}</dd>
    <dt>expected</dt><dd>{html.escape(text(row.get('expected_reading')))}</dd>
    <dt>human heard</dt><dd>{html.escape(text(row.get('human_heard_reading')))}</dd>
    <dt>surface hits</dt><dd>{html.escape(' | '.join(row.get('surface_hits') or []))}</dd>
    <dt>negative hits</dt><dd>{html.escape(' | '.join(row.get('negative_hits') or []))}</dd>
  </dl>
  <p class="transcript">{html.escape(text(row.get('asr_text')))}</p>
</article>"""
        )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
body{{font:15px/1.55 system-ui,sans-serif;margin:0;background:#f5f7fa;color:#172033}}
main{{max-width:1100px;margin:32px auto;padding:0 20px}}h1{{font-size:26px}}
nav{{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0}}button{{padding:7px 11px;border:1px solid #bcc5d3;background:white;border-radius:5px;cursor:pointer}}
article{{background:white;border:1px solid #dbe1e9;border-radius:6px;padding:16px;margin:12px 0}}
header{{display:flex;gap:12px;flex-wrap:wrap}}header span{{color:#536079}}
dl{{display:grid;grid-template-columns:110px 1fr;margin:12px 0}}dt{{font-weight:650;color:#536079}}dd{{margin:0}}
.transcript{{padding:12px;background:#f3f5f8;border-left:3px solid #4d739c;white-space:pre-wrap}}
</style></head><body><main><h1>{html.escape(title)}</h1>
<nav><button onclick="filterRows('all')">all</button>
<button onclick="filterRows('surface_correct_only')">surface only</button>
<button onclick="filterRows('negative_only')">negative only</button>
<button onclick="filterRows('surface_and_negative')">both</button>
<button onclick="filterRows('no_predefined_form')">no match</button></nav>
{''.join(cards)}</main><script>
function filterRows(value){{document.querySelectorAll('article').forEach(x=>x.hidden=value!=='all'&&x.dataset.relation!==value)}}
</script></body></html>"""
    path.write_text(document, encoding="utf-8")


def main() -> None:
    full = [score_row(row) for row in load_latest(FULL_RESULTS)]
    aligned = [score_row(row) for row in load_latest(ALIGNED_RESULTS)]
    if len(full) != 220:
        raise RuntimeError(f"expected 220 full results, found {len(full)}")
    if len(aligned) != 46:
        raise RuntimeError(f"expected 46 aligned results, found {len(aligned)}")

    confirmed = apply_occurrence_review([
        row for row in full if row["human_audit_outcome"] == "confirmed masked"
    ])
    confirmed_by_tts = {
        system: [row for row in confirmed if row["tts_system"] == system]
        for system in sorted({row["tts_system"] for row in confirmed})
    }

    full_mimo_by_probe = {
        row["probe_candidate_id"]: row
        for row in confirmed
        if row["tts_system"] == "MiMo-V2.5-TTS API"
    }
    paired = []
    for clip in aligned:
        full_row = full_mimo_by_probe[clip["probe_candidate_id"]]
        paired.append(
            {
                "probe_candidate_id": clip["probe_candidate_id"],
                "full_relation": full_row["automatic_asr_relation"],
                "clip_relation": clip["automatic_asr_relation"],
            }
        )

    summary = {
        "asr_control": (
            "Paraformer-zh v2.0.4 with FSMN-VAD v2.0.4, no punctuation "
            "model, no hotword, and no external language model. The original "
            "call used use_itn=False; a paired flag toggle produced identical "
            "transcripts and is not interpreted as an ITN ablation"
        ),
        "full_audio": {
            "all_rows": len(full),
            "errors": sum(bool(text(row.get("error"))) for row in full),
            "previously_labeled_confirmed_masked_rows": len(confirmed),
            "confirmed_relation_counts": relation_counts(confirmed),
            "occurrence_reviewed_counts": dict(
                Counter(row["reviewed_paraformer_relation"] for row in confirmed)
            ),
            "by_tts": {
                system: {
                    "rows": len(rows),
                    "relation_counts": relation_counts(rows),
                    "occurrence_reviewed_counts": dict(
                        Counter(row["reviewed_paraformer_relation"] for row in rows)
                    ),
                }
                for system, rows in confirmed_by_tts.items()
            },
        },
        "aligned_mimo_clips": {
            "rows": len(aligned),
            "errors": sum(bool(text(row.get("error"))) for row in aligned),
            "relation_counts": relation_counts(aligned),
            "exact_surface_correct_recovery": sum(
                row["automatic_asr_relation"]
                in {"surface_correct_only", "surface_and_negative"}
                for row in aligned
            ),
            "full_to_clip_relation_counts": dict(
                Counter(
                    f"{row['full_relation']} -> {row['clip_relation']}" for row in paired
                )
            ),
        },
        "interpretation_boundary": (
            "Automatic matching is separator-normalized and conservative. "
            "Rows with both or neither predefined forms require transcript "
            "review; Paraformer output is not treated as audio ground truth."
        ),
    }

    write_csv(RESULT_DIR / "paraformer_confirmed_97_transcript_audit.csv", confirmed)
    write_csv(RESULT_DIR / "paraformer_aligned_46_transcript_audit.csv", aligned)
    write_review_html(
        RESULT_DIR / "paraformer_confirmed_97_transcript_audit.html",
        confirmed,
        "Paraformer Confirmed-Masked Transcript Audit (n=97)",
    )
    write_review_html(
        RESULT_DIR / "paraformer_aligned_46_transcript_audit.html",
        aligned,
        "Paraformer Aligned-Clip Transcript Audit (n=46)",
    )
    (RESULT_DIR / "paraformer_targeted_control_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    markdown = [
        "# Paraformer-zh Targeted ASR Control",
        "",
        f"- Full audio transcribed: **{len(full)}**",
        f"- Previously labeled confirmed-masked cases analyzed: **{len(confirmed)}**",
        f"- Aligned MiMo clips transcribed: **{len(aligned)}**",
        "",
        "## Conservative Automatic Relation Counts",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "The automatic relation is an audit aid, not a replacement for human listening.",
    ]
    (RESULT_DIR / "paraformer_targeted_control_summary.md").write_text(
        "\n".join(markdown) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
