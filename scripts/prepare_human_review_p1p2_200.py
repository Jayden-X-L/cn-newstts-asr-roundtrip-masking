#!/usr/bin/env python3
"""Build P1 human review package for the frozen 200-case sample.

Outputs:
- mvp_eval/p1p2/human_review_200.xlsx
- mvp_eval/p1p2/human_review_200_primary.html
- mvp_eval/p1p2/human_review_200_iaa_r2.html
- mvp_eval/p1p2/human_review_200_iaa_r3.html
- mvp_eval/p1p2/human_review_200_assignments.csv

The HTML pages contain form fields and an "Export JSON" button. The exported
JSON can later be merged with a scorer script.
"""

from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path("PROJECT_ROOT_PLACEHOLDER")
P1P2 = ROOT / "mvp_eval" / "p1p2"
FROZEN = P1P2 / "p1p2_frozen_200_cases.xlsx"
RESULTS = P1P2 / "p1p2_tts_asr_raw_structured_results.xlsx"
OUT_XLSX = P1P2 / "human_review_200.xlsx"
ASSIGN_CSV = P1P2 / "human_review_200_assignments.csv"
AUDIO_DIR = ROOT / "mvp_eval" / "audio"


def parse_spans(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, str) and value.strip():
        try:
            return json.loads(value)
        except Exception:
            return []
    return []


def esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def rel_audio(path: Path, html_out: Path) -> str:
    try:
        return str(path.resolve().relative_to(html_out.parent.resolve()))
    except ValueError:
        return str(path)


def make_key_spans(spans: list[dict[str, Any]], limit: int = 16) -> str:
    lines = []
    for sp in spans[:limit]:
        wrong = sp.get("wrong_readings") or []
        wrong_txt = f" | wrong: {' / '.join(map(str, wrong[:4]))}" if wrong else ""
        lines.append(f"{sp.get('span')} => {sp.get('reading')} [{sp.get('type')}]{wrong_txt}")
    if len(spans) > limit:
        lines.append(f"... +{len(spans) - limit} more")
    return "\n".join(lines)


def pick_iaa_cases(df: pd.DataFrame, n: int = 30) -> set[str]:
    targets = {
        "cdrd_entity": 10,
        "cdrd_polyphone": 10,
        "non_cdrd": 10,
    }
    chosen: list[str] = []
    for label, target in targets.items():
        sub = df[df["cdrd_label"].eq(label)].copy()
        sub = sub.sort_values(["total_spans", "case_id"], ascending=[False, True])
        chosen.extend(sub.head(target)["case_id"].astype(str).tolist())
    if len(chosen) < n:
        rest = df[~df["case_id"].astype(str).isin(chosen)].sort_values(["total_spans", "case_id"], ascending=[False, True])
        chosen.extend(rest.head(n - len(chosen))["case_id"].astype(str).tolist())
    return set(chosen[:n])


def build_review_rows() -> pd.DataFrame:
    frozen = pd.read_excel(FROZEN)
    results = pd.read_excel(RESULTS) if RESULTS.exists() else pd.DataFrame()
    if not results.empty:
        results["error"] = results.get("error", "").fillna("").astype(str).replace("nan", "")
    rows = []
    by_case_pipe = {}
    if not results.empty:
        for _, r in results.iterrows():
            by_case_pipe[(str(r["case_id"]), str(r["pipeline"]))] = r

    for _, r in frozen.iterrows():
        case_id = str(r["case_id"])
        spans = parse_spans(r["risk_spans_json"])
        raw = by_case_pipe.get((case_id, "raw"))
        structured = by_case_pipe.get((case_id, "structured"))
        raw_audio = str(raw.get("audio_path")) if raw is not None and raw.get("audio_path") else str(AUDIO_DIR / "raw" / f"{case_id}.wav")
        structured_audio = str(structured.get("audio_path")) if structured is not None and structured.get("audio_path") else str(AUDIO_DIR / "structured" / f"{case_id}.wav")
        rows.append({
            "freeze_id": r["freeze_id"],
            "case_id": case_id,
            "source": r["source"],
            "cdrd_label": r["cdrd_label"],
            "domain": r["domain"],
            "risk_types": r["risk_types"],
            "total_spans": len(spans),
            "raw_text": r["raw_text"],
            "structured_tts_text": r["structured_text"],
            "key_risk_spans": make_key_spans(spans),
            "raw_audio_path": raw_audio,
            "structured_audio_path": structured_audio,
            "raw_asr_text": "" if raw is None else raw.get("asr_text", ""),
            "structured_asr_text": "" if structured is None else structured.get("asr_text", ""),
            "raw_auto_acc": "" if raw is None else raw.get("risk_span_audio_accuracy", ""),
            "structured_auto_acc": "" if structured is None else structured.get("risk_span_audio_accuracy", ""),
            "human_raw_correct": "",
            "human_structured_correct": "",
            "better_pipeline": "raw / structured / tie / unclear",
            "major_errors_raw": "",
            "major_errors_structured": "",
            "notes": "",
        })
    return pd.DataFrame(rows)


def write_xlsx(review_df: pd.DataFrame) -> None:
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as writer:
        review_df.to_excel(writer, sheet_name="review", index=False)
        ws = writer.sheets["review"]
        widths = {
            "A": 12, "B": 20, "C": 12, "D": 16, "E": 12,
            "F": 42, "G": 12, "H": 58, "I": 58, "J": 72,
            "K": 34, "L": 34, "M": 48, "N": 48, "S": 28,
            "T": 36, "U": 36, "V": 40,
        }
        for col, width in widths.items():
            ws.column_dimensions[col].width = width
        header = [cell.value for cell in ws[1]]
        for name in ("raw_audio_path", "structured_audio_path"):
            col_idx = header.index(name) + 1
            for row_i in range(2, ws.max_row + 1):
                cell = ws.cell(row=row_i, column=col_idx)
                path = str(cell.value or "")
                if not path:
                    continue
                display = path.rsplit("/", 1)[-1]
                cell.value = f'=HYPERLINK("file://{path}","{display}")'
                cell.style = "Hyperlink"
        for row in ws.iter_rows():
            for cell in row:
                cell.alignment = cell.alignment.copy(wrap_text=True, vertical="top")


def assignment_rows(review_df: pd.DataFrame) -> pd.DataFrame:
    iaa = pick_iaa_cases(review_df)
    rows = []
    for _, r in review_df.iterrows():
        rows.append({
            "assignment_id": f"primary_{r['freeze_id']}",
            "annotator": "primary",
            "freeze_id": r["freeze_id"],
            "case_id": r["case_id"],
            "is_iaa": False,
        })
        if r["case_id"] in iaa:
            for annotator in ("iaa_r2", "iaa_r3"):
                rows.append({
                    "assignment_id": f"{annotator}_{r['freeze_id']}",
                    "annotator": annotator,
                    "freeze_id": r["freeze_id"],
                    "case_id": r["case_id"],
                    "is_iaa": True,
                })
    return pd.DataFrame(rows)


def write_html(review_df: pd.DataFrame, assignments: pd.DataFrame, annotator: str) -> None:
    html_out = P1P2 / f"human_review_200_{annotator}.html"
    case_ids = assignments[assignments["annotator"].eq(annotator)]["case_id"].astype(str).tolist()
    sub = review_df[review_df["case_id"].astype(str).isin(case_ids)].copy()
    rows_html = []
    for _, r in sub.iterrows():
        raw_audio = rel_audio(Path(r["raw_audio_path"]), html_out)
        struct_audio = rel_audio(Path(r["structured_audio_path"]), html_out)
        rows_html.append(f"""
<section class="case" data-case-id="{esc(r['case_id'])}" data-freeze-id="{esc(r['freeze_id'])}">
  <div class="meta">
    <b>{esc(r['freeze_id'])}</b> · {esc(r['case_id'])} · {esc(r['source'])} · {esc(r['cdrd_label'])} · {esc(r['domain'])}<br>
    <span>{esc(r['risk_types'])}</span> · total_spans={esc(r['total_spans'])}
  </div>
  <div class="grid">
    <div><h3>Raw Text</h3><p>{esc(r['raw_text'])}</p></div>
    <div><h3>Structured TTS Text</h3><p>{esc(r['structured_tts_text'])}</p></div>
    <div><h3>Key Risk Spans</h3><pre>{esc(r['key_risk_spans'])}</pre></div>
  </div>
  <div class="audio-grid">
    <div><h3>Raw</h3><audio controls preload="none" src="{esc(raw_audio)}"></audio><p class="asr">{esc(r['raw_asr_text'])}</p></div>
    <div><h3>Structured</h3><audio controls preload="none" src="{esc(struct_audio)}"></audio><p class="asr">{esc(r['structured_asr_text'])}</p></div>
  </div>
  <div class="form-row">
    <label>raw correct <input type="number" min="0" max="{esc(r['total_spans'])}" step="1" name="human_raw_correct"></label>
    <label>structured correct <input type="number" min="0" max="{esc(r['total_spans'])}" step="1" name="human_structured_correct"></label>
    <label>better
      <select name="better_pipeline">
        <option value=""></option><option>raw</option><option>structured</option><option>tie</option><option>unclear</option>
      </select>
    </label>
    <label>notes <input type="text" name="notes"></label>
  </div>
</section>
""")
    page = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>CN-NewsTTS Human Review 200 - {esc(annotator)}</title>
<style>
body{{font-family:-apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif;margin:24px;color:#20242a;line-height:1.45;}}
h1{{font-size:22px;margin:0 0 6px;}} .note{{font-size:13px;color:#59636e;margin-bottom:18px;}}
.case{{border:1px solid #d8dee4;border-radius:8px;padding:14px;margin:0 0 18px;background:#fff;}}
.meta{{font-size:13px;color:#4b5563;margin-bottom:10px;}}
.grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;}}
.grid div,.audio-grid div{{border:1px solid #e5e7eb;background:#f9fafb;border-radius:6px;padding:10px;}}
h3{{font-size:14px;margin:0 0 8px;color:#1f5fbf;}}
pre,p{{white-space:pre-wrap;margin:0;font-size:13px;}} pre{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;}}
.audio-grid{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px;}}
audio{{width:100%;}} .asr{{font-size:12px;color:#59636e;margin-top:8px;}}
.form-row{{display:flex;gap:14px;flex-wrap:wrap;align-items:center;margin-top:12px;font-size:13px;}}
input,select{{font:inherit;padding:4px 6px;}} input[type=number]{{width:64px;}} input[type=text]{{width:360px;}}
button{{font:inherit;padding:8px 12px;border:1px solid #1f5fbf;border-radius:6px;background:#1f5fbf;color:#fff;cursor:pointer;}}
</style></head><body>
<h1>CN-NewsTTS Human Review 200 - {esc(annotator)}</h1>
<p class="note">按 Key Risk Spans 计数每条音频读对几个 span。填完点击 Export JSON，把下载文件交回合并。</p>
<button onclick="exportJson()">Export JSON</button>
{''.join(rows_html)}
<script>
function exportJson(){{
  const rows = [...document.querySelectorAll('.case')].map(sec => {{
    const get = name => sec.querySelector(`[name="${{name}}"]`)?.value ?? '';
    return {{
      annotator: "{esc(annotator)}",
      freeze_id: sec.dataset.freezeId,
      case_id: sec.dataset.caseId,
      human_raw_correct: get('human_raw_correct'),
      human_structured_correct: get('human_structured_correct'),
      better_pipeline: get('better_pipeline'),
      notes: get('notes')
    }};
  }});
  const blob = new Blob([JSON.stringify(rows, null, 2)], {{type:'application/json'}});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'human_review_200_{esc(annotator)}.json';
  a.click();
}}
</script></body></html>
"""
    html_out.write_text(page, encoding="utf-8")


def main() -> None:
    P1P2.mkdir(parents=True, exist_ok=True)
    review_df = build_review_rows()
    write_xlsx(review_df)
    assignments = assignment_rows(review_df)
    assignments.to_csv(ASSIGN_CSV, index=False)
    for annotator in ("primary", "iaa_r2", "iaa_r3"):
        write_html(review_df, assignments, annotator)
    print(json.dumps({
        "review_rows": len(review_df),
        "assignment_rows": len(assignments),
        "assignments": assignments["annotator"].value_counts().to_dict(),
        "cdrd_label_counts": review_df["cdrd_label"].value_counts().to_dict(),
        "outputs": {
            "xlsx": str(OUT_XLSX),
            "assignments": str(ASSIGN_CSV),
            "html_primary": str(P1P2 / "human_review_200_primary.html"),
            "html_iaa_r2": str(P1P2 / "human_review_200_iaa_r2.html"),
            "html_iaa_r3": str(P1P2 / "human_review_200_iaa_r3.html"),
        },
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
