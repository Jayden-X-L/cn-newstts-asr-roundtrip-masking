"""Text-matching and numeral helpers preserved for the 2026 audit revision.

Matcher: original 2026-06-06 targeted-pool builder, with CSV-compatible input.
Numerals: CN-NewsTTS Bench v0.1 (MIT), Shijun Luo, 2026.
These functions identify candidates; they do not assign listening labels.
"""
from __future__ import annotations
import json
import re
from typing import Any

def norm_text(value):
    return "" if value is None else str(value)

TYPE_ORDER = ['sports_score', 'military_model', 'generation_label', 'quarter', 'hyphen_range', 'kw_kwh', 'nm_torque', 'vip88', 'voltage', 'tops_compute']

SPORTS_CONTEXT = ['比分', '战胜', '击败', '逆转', '晋级', '决赛', '半决赛', '夺冠', '冠军', 'CBA', 'NBA', 'WTT', 'WTA', '中超', '欧冠', '英超', '西甲', '意甲', '德甲', '比赛', '联赛', '世锦赛', '世界杯', '斯诺克', '篮球', '足球', '网球', '乒乓', '排球', '汤杯', '亚洲杯']

MILITARY_CONTEXT = ['战机', '军机', '空军', '导弹', '防空', '无人机', '轰炸机', '战斗机', '航母', '军方', '俄乌', '俄罗斯', '乌克兰', '北约', '美军', '军售', '击落', '军事']

REGEXES = {'sports_score': ['(?<!\\d)\\d{1,3}\\s*[-:：]\\s*\\d{1,3}(?!\\d)'], 'military_model': ['(?<![一-龥])(?:苏|伊尔|米格)\\s*[-－]\\s*\\d{1,3}[A-Z]?', '(?<![一-龥])(?:歼|运|轰|直)\\s*[-－]?\\s*\\d{1,3}[A-Z]?', '\\b(?:F|B|C|J|H|Y)-\\d{1,3}[A-Z]?\\b'], 'generation_label': ['(?:00|05|10|20|50|60|70|80|85|90|95)后'], 'quarter': ['\\b[Qq][1-4]\\b'], 'hyphen_range': ['(?<!\\d)\\d{1,4}\\s*[-–—－]\\s*\\d{1,4}(?!\\d)'], 'kw_kwh': ['\\d+(?:\\.\\d+)?\\s*(?:kW·h|KW·h|kWh|KWh|kwh|kW|KW|kw|千瓦时|千瓦)'], 'nm_torque': ['\\d+(?:\\.\\d+)?\\s*(?:N[·⋅.\\- ]?m|Nm|NM|牛米)'], 'vip88': ['88\\s*(?:VIP|vip)'], 'voltage': ['(?<![A-Za-z0-9.])\\d{1,4}(?:\\.\\d+)?\\s*[Vv](?![A-Za-z])'], 'tops_compute': ['(?:\\d+(?:\\.\\d+)?\\s*)?(?:TOPS|Tops|tops)', '算力']}

def parse_json_list(value):
    text = norm_text(value).strip()
    if not text:
        return []
    try:
        obj = json.loads(text)
    except Exception:
        return []
    return obj if isinstance(obj, list) else []

def dedupe(items):
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = re.sub('\\s+', '', norm_text(item))
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            out.append(cleaned)
    return out

def has_any(text, words):
    return any((w in text for w in words))

def looks_like_score_span(span):
    compact = re.sub('\\s+', '', span)
    m = re.fullmatch('(\\d{1,3})([-:：])(\\d{1,3})', compact)
    if not m:
        return True
    left = int(m.group(1))
    sep = m.group(2)
    right = int(m.group(3))
    if sep in {':', '：'}:
        return left <= 10 and right <= 10
    return True

def span_type_to_probe_type(span_type, span, text):
    if span_type in {'sports_score_hyphen', 'sports_score_colon'} and has_any(text, SPORTS_CONTEXT) and looks_like_score_span(span):
        return 'sports_score'
    if span_type == 'military_model_hyphen' and has_any(text, MILITARY_CONTEXT):
        return 'military_model'
    if span_type == 'generation_label':
        return 'generation_label'
    if span_type in {'quarter_finance', 'quarter_product'}:
        return 'quarter'
    if span_type in {'range_hyphen', 'year_range_hyphen'}:
        return 'hyphen_range'
    if span_type == 'tech_unit':
        if re.search(REGEXES['kw_kwh'][0], span):
            return 'kw_kwh'
        if re.search(REGEXES['nm_torque'][0], span):
            return 'nm_torque'
        if re.search(REGEXES['voltage'][0], span):
            compact_text = re.sub('\\s+', '', text).upper()
            compact_span = re.sub('\\s+', '', span).upper()
            if f'{compact_span}IP' in compact_text:
                return None
            return 'voltage'
        if re.search(REGEXES['tops_compute'][0], span) or '算力' in span:
            return 'tops_compute'
    return None

def regex_matches(text, probe_type):
    if probe_type == 'sports_score' and (not has_any(text, SPORTS_CONTEXT)):
        return []
    if probe_type == 'military_model' and (not has_any(text, MILITARY_CONTEXT)):
        return []
    spans: list[str] = []
    for pat in REGEXES[probe_type]:
        spans.extend((m.group(0) for m in re.finditer(pat, text)))
    spans = dedupe(spans)
    if probe_type == 'sports_score':
        spans = [s for s in spans if looks_like_score_span(s)]
    return spans

def classify_case(row):
    text = f"{norm_text(row.get('raw_title'))}。{norm_text(row.get('raw_summary'))}。{norm_text(row.get('raw_text'))}"
    risk_spans = parse_json_list(row.get('risk_spans_json'))
    matched: dict[str, list[str]] = {k: [] for k in TYPE_ORDER}
    risk_lines: dict[str, list[str]] = {k: [] for k in TYPE_ORDER}
    for sp in risk_spans:
        span = norm_text(sp.get('span'))
        probe_type = span_type_to_probe_type(norm_text(sp.get('type')), span, text)
        if not probe_type:
            continue
        matched[probe_type].append(span)
        wrong = sp.get('wrong_readings') or []
        wrong_txt = f" | wrong: {' / '.join(map(str, wrong[:4]))}" if wrong else ''
        risk_lines[probe_type].append(f"{span} => {norm_text(sp.get('reading'))} [{norm_text(sp.get('type'))}]{wrong_txt}")
    for probe_type in TYPE_ORDER:
        matched[probe_type].extend(regex_matches(text, probe_type))
        matched[probe_type] = dedupe(matched[probe_type])
        risk_lines[probe_type] = dedupe(risk_lines[probe_type])
    matched = {k: v for k, v in matched.items() if v}
    risk_lines = {k: v for k, v in risk_lines.items() if v}
    return (matched, risk_lines)

DIGITS = '零一二三四五六七八九'

def num_zh(n: int) -> str:
    if n < 0 or n > 999:
        raise ValueError(n)
    if n < 10:
        return DIGITS[n]
    if n < 20:
        return '十' + (DIGITS[n % 10] if n % 10 else '')
    if n < 100:
        tens, ones = divmod(n, 10)
        return DIGITS[tens] + '十' + (DIGITS[ones] if ones else '')
    hundreds, rest = divmod(n, 100)
    out = DIGITS[hundreds] + '百'
    if rest == 0:
        return out
    if rest < 10:
        return out + '零' + DIGITS[rest]
    if rest < 20:
        return out + '一' + num_zh(rest)
    return out + num_zh(rest)

def digit_zh(value: int | str) -> str:
    return ''.join((DIGITS[int(ch)] for ch in str(value)))
