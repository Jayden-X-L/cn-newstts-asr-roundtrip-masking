import base64
import json
import os
import time
import urllib.request
from pathlib import Path

import pandas as pd
import requests


BASE = Path(__file__).resolve().parent
EVAL_DIR = BASE / "mvp_eval"
CONFIG_PATH = BASE / "xiaomi_api_config.json"
INPUT_XLSX = Path(os.environ.get("EVAL_INPUT_XLSX",
                                  str(EVAL_DIR / "eval_50_input.xlsx")))
AUDIO_DIR = EVAL_DIR / "audio"
RESULT_XLSX = Path(os.environ.get("EVAL_RESULT_XLSX",
                                   str(EVAL_DIR / "tts_asr_eval_50_results.xlsx")))


def json_path(obj, path):
    cur = obj
    for part in path.split("."):
        if part == "":
            continue
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def render(value, ctx):
    if isinstance(value, str):
        out = value
        for k, v in ctx.items():
            if isinstance(v, (dict, list)):
                v = json.dumps(v, ensure_ascii=False)
            out = out.replace("${" + k + "}", str(v))
        return out
    if isinstance(value, dict):
        return {k: render(v, ctx) for k, v in value.items()}
    if isinstance(value, list):
        return [render(v, ctx) for v in value]
    return value


def normalize_for_match(text):
    return str(text).replace(" ", "").replace("，", "").replace("。", "").replace(",", "")


def post_json(cfg, body, api_key):
    headers = render(cfg.get("headers", {}), {"api_key": api_key})
    max_attempts = int(os.environ.get("REQUEST_MAX_ATTEMPTS", cfg.get("max_attempts", 3) or 3))
    backoff = float(os.environ.get("REQUEST_BACKOFF_SECONDS", "4"))
    for attempt in range(max_attempts):
        resp = requests.request(
            cfg.get("method", "POST"),
            cfg["url"],
            headers=headers,
            json=body,
            timeout=cfg.get("timeout_seconds") or 120,
            proxies={"http": None, "https": None},
        )
        if resp.status_code in {429, 500, 502, 503, 504} and attempt < max_attempts - 1:
            retry_after = resp.headers.get("retry-after")
            wait = float(retry_after) if retry_after else backoff * (2 ** attempt)
            time.sleep(wait)
            continue
        resp.raise_for_status()
        ctype = resp.headers.get("content-type", "")
        if "application/json" in ctype or resp.text.strip().startswith("{"):
            return resp.json(), resp.content
        return None, resp.content


def call_tts(config, text, pronunciation_dict, audio_path):
    api_key = os.environ[config.get("api_key_env", "XIAOMI_MIMO_API_KEY")]
    tts_cfg = dict(config["tts"])
    tts_cfg["timeout_seconds"] = config.get("request_timeout_seconds", 120)
    body = render(tts_cfg["body_template"], {
        "text": text,
        "pronunciation_dict": pronunciation_dict,
    })
    data, raw = post_json(tts_cfg, body, api_key)
    audio_spec = tts_cfg.get("response_audio", {"type": "binary"})
    typ = audio_spec.get("type", "binary")
    if typ == "binary":
        audio = raw
    else:
        val = json_path(data, audio_spec["json_path"])
        if typ == "base64":
            audio = base64.b64decode(val)
        elif typ == "hex":
            audio = bytes.fromhex(val)
        elif typ == "url":
            audio = urllib.request.urlopen(val, timeout=120).read()
        else:
            raise ValueError(f"Unsupported TTS audio response type: {typ}")
    audio_path.write_bytes(audio)
    return data


def call_asr(config, audio_path):
    api_key = os.environ[config.get("api_key_env", "XIAOMI_MIMO_API_KEY")]
    asr_cfg = dict(config["asr"])
    asr_cfg["timeout_seconds"] = config.get("request_timeout_seconds", 120)
    audio_bytes = audio_path.read_bytes()
    body = render(asr_cfg["body_template"], {
        "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
        "audio_path": str(audio_path),
    })
    data, _ = post_json(asr_cfg, body, api_key)
    return json_path(data, asr_cfg["response_text"]["json_path"]), data


def eval_spans(asr_text, risk_spans):
    norm_asr = normalize_for_match(asr_text)
    out = []
    for sp in risk_spans:
        expected = normalize_for_match(sp["reading"])
        correct = expected in norm_asr
        out.append({
            "span": sp["span"],
            "type": sp["type"],
            "expected": sp["reading"],
            "correct": correct,
        })
    return out


def main(limit=None):
    if not CONFIG_PATH.exists():
        raise SystemExit(f"Missing config: {CONFIG_PATH}. Copy xiaomi_api_config.template.json to xiaomi_api_config.json and fill endpoints/model ids.")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if os.environ.get("REQUEST_TIMEOUT_SECONDS"):
        config["request_timeout_seconds"] = int(os.environ["REQUEST_TIMEOUT_SECONDS"])
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_excel(INPUT_XLSX)
    if limit:
        df = df.head(limit)
    rows = []
    completed = set()
    if RESULT_XLSX.exists() and not os.environ.get("EVAL_RESTART"):
        old = pd.read_excel(RESULT_XLSX)
        rows = old.to_dict("records")
        for _, old_row in old.iterrows():
            err = old_row.get("error", "")
            err = "" if pd.isna(err) else str(err).strip()
            if not err:
                completed.add((str(old_row.get("case_id")), str(old_row.get("pipeline"))))
    for i, row in df.iterrows():
        case_id = row["case_id"]
        pipeline = row["pipeline"]
        if (str(case_id), str(pipeline)) in completed:
            print(f"[{i + 1}/{len(df)}] {case_id} {pipeline} skipped")
            continue
        audio_format = config.get("tts", {}).get("audio_format", "wav")
        audio_path = AUDIO_DIR / pipeline / f"{case_id}.{audio_format}"
        audio_path.parent.mkdir(exist_ok=True)
        risk_spans = json.loads(row["risk_spans_json"])
        pronunciation_dict = json.loads(row.get("pronunciation_dict_json") or "{}")
        started = time.time()
        error = ""
        asr_text = ""
        tts_resp = None
        asr_resp = None
        try:
            tts_resp = call_tts(config, row["tts_input_text"], pronunciation_dict, audio_path)
            asr_text, asr_resp = call_asr(config, audio_path)
        except Exception as exc:
            error = repr(exc)
        span_eval = eval_spans(asr_text, risk_spans) if asr_text else []
        correct = sum(1 for x in span_eval if x["correct"])
        total = len(span_eval)
        rows.append({
            **row.to_dict(),
            "audio_path": str(audio_path),
            "asr_text": asr_text,
            "risk_span_eval_json": json.dumps(span_eval, ensure_ascii=False),
            "risk_span_correct_count": correct,
            "risk_span_total_count": total,
            "risk_span_audio_accuracy": correct / total if total else 0,
            "latency_seconds": round(time.time() - started, 3),
            "error": error,
            "tts_response_json": json.dumps(tts_resp, ensure_ascii=False)[:2000] if tts_resp else "",
            "asr_response_json": json.dumps(asr_resp, ensure_ascii=False)[:2000] if asr_resp else "",
        })
        pd.DataFrame(rows).to_excel(RESULT_XLSX, index=False)
        print(f"[{i + 1}/{len(df)}] {case_id} {pipeline} acc={rows[-1]['risk_span_audio_accuracy']:.2f} err={bool(error)}")
        row_sleep = float(os.environ.get("EVAL_ROW_SLEEP_SECONDS", "0") or "0")
        if row_sleep:
            time.sleep(row_sleep)
    print(f"Saved: {RESULT_XLSX}")


if __name__ == "__main__":
    limit = os.environ.get("EVAL_LIMIT")
    main(int(limit) if limit else None)
