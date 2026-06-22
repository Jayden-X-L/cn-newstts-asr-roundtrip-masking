#!/usr/bin/env python3
"""Run MiMo strict ASR over a JSONL manifest.

The input rows need at least `case_id`, `pipeline`, and `audio_path`.
Rows are written incrementally so the job can resume safely.
"""

from __future__ import annotations

import json
import os
import time
import base64
from pathlib import Path

import requests


BASE = Path(__file__).resolve().parents[1]
CONFIG_PATH = Path(os.environ.get("MIMO_CONFIG_PATH", str(BASE / "xiaomi_api_config.json")))
INPUT = Path(os.environ["MIMO_JSONL_INPUT"])
OUTPUT = Path(os.environ["MIMO_JSONL_OUTPUT"])
LIMIT = int(os.environ.get("MIMO_JSONL_LIMIT", "0") or 0)
PREFIX_FROM = os.environ.get("MIMO_AUDIO_PATH_PREFIX_FROM", "")
PREFIX_TO = os.environ.get("MIMO_AUDIO_PATH_PREFIX_TO", "")
BAD_TEXT_MAX_ATTEMPTS = int(os.environ.get("MIMO_BAD_TEXT_MAX_ATTEMPTS", "3") or 3)
BAD_TEXT_BACKOFF_SECONDS = float(os.environ.get("MIMO_BAD_TEXT_BACKOFF_SECONDS", "3") or 3)


REFUSAL_PATTERNS = [
    "您发送",
    "不是音频文件",
    "无法转写",
    "抱歉，我无法",
    "我无法接收",
    "无法播放音频",
    "请提供音频文件",
    "上传音频",
    "没有附上音频",
    "没有收到音频",
    "并没有附带音频",
]


def json_path(obj: object, path: str) -> object:
    cur = obj
    for part in path.split("."):
        if part == "":
            continue
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def render(value: object, ctx: dict[str, object]) -> object:
    if isinstance(value, str):
        out = value
        for key, replacement in ctx.items():
            if isinstance(replacement, (dict, list)):
                replacement = json.dumps(replacement, ensure_ascii=False)
            out = out.replace("${" + key + "}", str(replacement))
        return out
    if isinstance(value, dict):
        return {key: render(replacement, ctx) for key, replacement in value.items()}
    if isinstance(value, list):
        return [render(item, ctx) for item in value]
    return value


def post_json(cfg: dict, body: dict, api_key: str) -> dict:
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
        return resp.json()
    raise RuntimeError("unreachable")


def call_asr(config: dict, audio_path: Path) -> tuple[str, dict]:
    api_key = os.environ[config.get("api_key_env", "MIMO_API_KEY")]
    asr_cfg = dict(config["asr"])
    asr_cfg["timeout_seconds"] = config.get("request_timeout_seconds", 120)
    audio_base64 = base64.b64encode(audio_path.read_bytes()).decode("utf-8")
    body = render(asr_cfg["body_template"], {
        "audio_base64": audio_base64,
        "audio_path": str(audio_path),
    })
    data = post_json(asr_cfg, body, api_key)
    return str(json_path(data, asr_cfg["response_text"]["json_path"])), data


def load_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows[:LIMIT] if LIMIT else rows


def completed_keys(path: Path) -> set[tuple[str, str]]:
    if not path.exists():
        return set()
    done = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                row = json.loads(line)
            except Exception:
                continue
            if not str(row.get("asr_error") or "").strip() and not bool(row.get("asr_needs_retry_or_review")):
                done.add((str(row.get("case_id")), str(row.get("pipeline"))))
    return done


def map_audio_path(path: str) -> Path:
    if PREFIX_FROM and PREFIX_TO and path.startswith(PREFIX_FROM):
        return Path(PREFIX_TO + path[len(PREFIX_FROM):])
    return Path(path)


def looks_bad(text: str) -> bool:
    s = (text or "").strip()
    return (not s) or any(p in s for p in REFUSAL_PATTERNS)


def main() -> None:
    if not CONFIG_PATH.exists():
        raise SystemExit(f"missing config: {CONFIG_PATH}")
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    key_name = config.get("api_key_env", "MIMO_API_KEY")
    if not os.environ.get(key_name):
        raise SystemExit(f"{key_name} is not set")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows = load_jsonl(INPUT)
    done = completed_keys(OUTPUT)
    print(json.dumps({
        "input": str(INPUT),
        "output": str(OUTPUT),
        "rows": len(rows),
        "already_done": len(done),
        "config": str(CONFIG_PATH),
        "api_key_env": key_name,
        "audio_prefix_from": PREFIX_FROM,
        "audio_prefix_to": PREFIX_TO,
    }, ensure_ascii=False), flush=True)

    with OUTPUT.open("a", encoding="utf-8") as out_f:
        for i, row in enumerate(rows, 1):
            key = (str(row["case_id"]), str(row["pipeline"]))
            if key in done:
                continue
            audio_path = map_audio_path(str(row["audio_path"]))
            started = time.time()
            text = ""
            err = ""
            raw_response = None
            attempts = 0
            if not audio_path.exists():
                err = repr(FileNotFoundError(str(audio_path)))
            else:
                for attempt in range(1, BAD_TEXT_MAX_ATTEMPTS + 1):
                    attempts = attempt
                    try:
                        text, raw_response = call_asr(config, audio_path)
                        err = ""
                    except Exception as exc:
                        text = ""
                        raw_response = None
                        err = repr(exc)
                    if err or not looks_bad(text):
                        break
                    if attempt < BAD_TEXT_MAX_ATTEMPTS:
                        time.sleep(BAD_TEXT_BACKOFF_SECONDS)

            rec = dict(row)
            if "error" in rec and "tts_error" not in rec:
                rec["tts_error"] = rec.get("error")
            if "latency_seconds" in rec and "tts_latency_seconds" not in rec:
                rec["tts_latency_seconds"] = rec.get("latency_seconds")
            rec["mimo_asr_audio_path"] = str(audio_path)
            rec["asr_model"] = "mimo-v2.5"
            rec["asr_protocol"] = "mimo_strict"
            rec["asr_text"] = text or ""
            rec["asr_error"] = err
            rec["asr_needs_retry_or_review"] = looks_bad(text) if not err else True
            rec["asr_attempts"] = attempts
            rec["asr_latency_seconds"] = round(time.time() - started, 3)
            rec["asr_response_json"] = json.dumps(raw_response, ensure_ascii=False) if raw_response else ""
            out_f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out_f.flush()
            print(
                f"[{i}/{len(rows)}] {row['case_id']} {row['pipeline']} "
                f"len={len(text or '')} err={bool(err)} bad={rec['asr_needs_retry_or_review']}",
                flush=True,
            )


if __name__ == "__main__":
    main()
