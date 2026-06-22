"""Improved auto evaluator for CN-NewsTTS roundtrip results (strict v2).

Logic:
1. For each risk span, compute negative patterns (wrong readings) and positive
   patterns (correct readings, allowing surface forms only when ASR cannot
   distinguish between right/wrong reading).
2. If the ASR text contains any wrong pattern: span = wrong.
3. Else if it contains a correct pattern: span = correct.
4. Else span = unknown (counts as wrong).
5. Polyphone / foreign name types require human listening; excluded from auto.
"""
import json
import os
import re
from pathlib import Path

import pandas as pd


BASE = Path(__file__).resolve().parent
RES = Path(os.environ.get("RESCORE_INPUT_XLSX", str(BASE / "mvp_eval" / "tts_asr_eval_50_results.xlsx")))
OUT = Path(os.environ.get("RESCORE_OUTPUT_XLSX", str(BASE / "mvp_eval" / "tts_asr_eval_50_results.scored.xlsx")))
SUMMARY = Path(os.environ.get("RESCORE_SUMMARY_JSON", str(BASE / "mvp_eval" / "tts_asr_eval_50_summary.json")))

CHINESE_DIGITS = {
    "零": "0", "一": "1", "幺": "1", "二": "2", "两": "2",
    "三": "3", "四": "4", "五": "5", "六": "6", "七": "7",
    "八": "8", "九": "9",
}

HUMAN_ONLY_TYPES = {"polyphone_disambiguation", "foreign_name_pronunciation"}


def _zh_per_digit_to_arabic(text):
    return "".join(CHINESE_DIGITS.get(ch, ch) for ch in text)


def _normalize_text(s):
    if s is None:
        return ""
    s = str(s)
    s = re.sub(r"\s+", "", s)
    s = s.replace("·", "").replace("：", ":").replace("，", ",").replace("。", "")
    return s


def _arabic_to_zh(n):
    table = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九"]
    return table[n] if 0 <= n < 10 else str(n)


def _year_magnitude_wrong(year_str):
    # Build the wrong "two-thousand…" reading for a 4-digit year.
    # 2025 -> 两千零二十五年; 2010 -> 两千一十年; 2011 -> 两千一十一年; 2020 -> 两千零二十年
    try:
        year = int(year_str)
    except Exception:
        return []
    if year < 1900 or year > 2099:
        return []
    if year < 2000:
        return []
    last_two = year % 100
    base = "两千"
    if last_two == 0:
        body = ""
    elif last_two < 10:
        body = "零" + _arabic_to_zh(last_two)
    elif last_two < 20:
        body = "一十"
        if last_two > 10:
            body += _arabic_to_zh(last_two - 10)
    else:
        tens = last_two // 10
        ones = last_two % 10
        body = _arabic_to_zh(tens) + "十"
        if ones:
            body += _arabic_to_zh(ones)
    return [base + body]


def positive_patterns(span, reading, span_type):
    expected = _normalize_text(reading)
    surface = _normalize_text(span)
    pats = {expected}

    if span_type == "fixed_abbreviation":
        # "A I" or "AI" both indicate digit-by-letter reading. Wrong would be 翻译成中文.
        pats.add(expected.replace(" ", ""))
        pats.add(surface.upper())
    if span_type == "percentage":
        # ASR usually normalizes "百分之三十八点五" -> "38.5%".
        m = re.match(r"(\d+(?:\.\d+)?)%", surface)
        if m:
            pats.add(m.group(0))
            pats.add("百分之" + m.group(1))
    if span_type == "year_with_suffix":
        # Correct read: 二零二五年; ASR may surface as 2025年 (same digit, ambiguous,
        # so we still treat 2025年 as positive — wrong magnitude form is in negatives).
        pats.add(expected)
        m = re.match(r"^(\d{4})年$", surface)
        if m:
            pats.add(m.group(0))
    if span_type == "year_bare":
        pats.add(expected)
        if re.fullmatch(r"\d+", surface):
            pats.add(surface)
    if span_type == "generation_label":
        # 八零后 should appear; surface "80后" also positive (wrong reading 八十后 in negatives).
        pats.add(expected)
        pats.add(surface)
    if span_type in {"sports_score_hyphen", "sports_score_colon"}:
        # Correct = "X比Y"; surface "X-Y" / "X:Y" is also positive because TTS may not have
        # been able to read but ASR normalized. Wrong is "X到Y" / "X除Y" in negatives.
        parts = re.findall(r"\d+", surface)
        if len(parts) == 2:
            pats.add(f"{parts[0]}比{parts[1]}")
    if span_type == "range_hyphen":
        parts = re.findall(r"\d+", surface)
        if len(parts) == 2:
            pats.add(f"{parts[0]}到{parts[1]}")
            pats.add(f"{parts[0]}至{parts[1]}")
    if span_type == "military_model_hyphen":
        # Correct: "苏二七"; surface "苏-27" / "苏27" considered positive (negatives carry wrong reads).
        pats.add(expected)
        pats.add(re.sub(r"-", "", surface))
        pats.add(_zh_per_digit_to_arabic(expected))
    if span_type == "quarter_finance":
        pats.add(expected)
    if span_type == "quarter_product":
        pats.add(expected)
        m = re.match(r"Q([1-4])", surface)
        if m:
            pats.add(f"Q{m.group(1)}")
    if span_type == "tech_unit":
        pats.add(expected)
    if span_type == "version_number":
        pats.add(expected)
        digits = re.sub(r"[^0-9\.]", "", surface)
        if digits:
            pats.add(digits)
    return {p for p in pats if p}


def negative_patterns(span, reading, span_type, wrong_readings):
    negs = set()
    surface = _normalize_text(span)
    for w in wrong_readings or []:
        w_norm = _normalize_text(w)
        if w_norm:
            negs.add(w_norm)

    if span_type == "year_with_suffix":
        m = re.match(r"^(\d{4})年$", surface)
        if m:
            for wf in _year_magnitude_wrong(m.group(1)):
                negs.add(wf + "年")
    if span_type == "year_bare":
        m = re.match(r"^(\d{4})$", surface)
        if m:
            for wf in _year_magnitude_wrong(m.group(1)):
                negs.add(wf)
    if span_type == "generation_label":
        negs.update({"八十后", "九十后", "幺零后", "零十后", "一十后"})
    if span_type == "sports_score_hyphen":
        parts = re.findall(r"\d+", surface)
        if len(parts) == 2:
            a, b = parts
            negs.update({f"{a}到{b}", f"{a}负{b}", f"{a}减{b}"})
    if span_type == "sports_score_colon":
        parts = re.findall(r"\d+", surface)
        if len(parts) == 2:
            a, b = parts
            negs.update({f"{a}除{b}", f"{a}冒号{b}"})
    if span_type == "range_hyphen":
        parts = re.findall(r"\d+", surface)
        if len(parts) == 2:
            a, b = parts
            negs.update({f"{a}负{b}", f"{a}减{b}"})
    if span_type == "percentage":
        m = re.match(r"(\d+(?:\.\d+)?)%", surface)
        if m:
            negs.update({f"{m.group(1)}百分号", f"百分号{m.group(1)}"})
    if span_type == "fixed_abbreviation":
        mp = {"AI": "人工智能", "GDP": "国内生产总值", "NBA": "美职篮"}
        if surface in mp:
            negs.add(mp[surface])
            if surface == "NBA":
                negs.add("全国篮球协会")
    if span_type == "military_model_hyphen":
        m = re.match(r"^(.+?)-(\d+)([A-Z]?)$", str(span))
        if m:
            prefix, num = m.group(1), m.group(2)
            negs.add(f"{prefix}负{num}")
            negs.add(f"{prefix}到{num}")
            negs.add(f"{prefix}减{num}")
    return {n for n in negs if n}


def evaluate_span(asr_norm, span, reading, span_type, wrong_readings=None):
    if span_type in HUMAN_ONLY_TYPES:
        return {
            "correct": None,
            "auto_match": None,
            "matched_token": None,
            "wrong_matched": None,
            "requires_human": True,
        }
    negs = negative_patterns(span, reading, span_type, wrong_readings)
    wrong_hit = next((w for w in sorted(negs, key=lambda c: -len(c)) if w and w in asr_norm), None)
    if wrong_hit:
        return {
            "correct": False,
            "auto_match": False,
            "matched_token": None,
            "wrong_matched": wrong_hit,
            "requires_human": False,
        }
    pats = positive_patterns(span, reading, span_type)
    hit = next((p for p in sorted(pats, key=lambda c: -len(c)) if p and p in asr_norm), None)
    return {
        "correct": hit is not None,
        "auto_match": hit is not None,
        "matched_token": hit,
        "wrong_matched": None,
        "requires_human": False,
    }


def main():
    df = pd.read_excel(RES)
    df["error"] = df["error"].fillna("").astype(str).replace("nan", "")
    out_rows = []
    span_records = []
    for _, row in df.iterrows():
        err = str(row.get("error") or "").strip()
        spans = []
        try:
            spans = json.loads(row.get("risk_spans_json") or "[]")
        except Exception:
            spans = []
        asr_norm = _normalize_text(row.get("asr_text"))
        new_eval = []
        autoable = 0
        autoable_correct = 0
        human_only = 0
        for sp in spans:
            res = evaluate_span(
                asr_norm,
                sp.get("span", ""),
                sp.get("reading", ""),
                sp.get("type", "other"),
                sp.get("wrong_readings"),
            )
            new_eval.append({**sp, **res})
            if res["requires_human"]:
                human_only += 1
            else:
                autoable += 1
                if res["correct"]:
                    autoable_correct += 1
            span_records.append({
                "case_id": row["case_id"],
                "pipeline": row["pipeline"],
                "domain": row.get("domain"),
                "type": sp.get("type"),
                "span": sp.get("span"),
                "reading": sp.get("reading"),
                "asr_text": row.get("asr_text"),
                "correct": res["correct"],
                "wrong_matched": res["wrong_matched"],
                "requires_human": res["requires_human"],
                "matched_token": res["matched_token"],
            })
        out_rows.append({
            **{k: row[k] for k in row.index if k != "risk_span_eval_json"},
            "risk_span_eval_json_v2": json.dumps(new_eval, ensure_ascii=False),
            "auto_total_spans": autoable,
            "auto_correct_spans": autoable_correct,
            "auto_accuracy": autoable_correct / autoable if autoable else None,
            "human_only_spans": human_only,
            "has_error": bool(err),
        })

    out_df = pd.DataFrame(out_rows)
    out_df.to_excel(OUT, index=False)

    span_df = pd.DataFrame(span_records)
    autoable_span = span_df[~span_df["requires_human"]].copy()

    summary = {
        "rows": int(len(out_df)),
        "errors": int(out_df["has_error"].sum()),
        "auto_accuracy_by_pipeline": (
            out_df.dropna(subset=["auto_accuracy"]).groupby("pipeline")["auto_accuracy"].agg(["count", "mean"]).round(4).to_dict("index")
        ),
        "per_type": (
            autoable_span.groupby(["type", "pipeline"])["correct"].agg(["count", "mean"]).round(4).reset_index().to_dict("records")
        ),
        "human_only_counts": {
            f"{t}|{p}": int(v)
            for (t, p), v in span_df[span_df["requires_human"]].groupby(["type", "pipeline"])["correct"].count().items()
        },
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k != "per_type"}, ensure_ascii=False, indent=2))
    print("\nper_type:")
    for r in summary["per_type"]:
        print(f"  {r['type']:30s} {r['pipeline']:12s} count={r['count']:>4}  mean={r['mean']:.3f}")


if __name__ == "__main__":
    main()
