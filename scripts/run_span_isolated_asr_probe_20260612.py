"""Span-isolated ASR probe for confirmed MiMo masked-error cases.

This probes whether full-sentence ASR masking decreases when the risk span is
cut out as a short local audio segment and transcribed independently.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "mvp_eval" / "span_isolated_asr_probe_20260612"
INPUT_JSON = ROOT / "mvp_eval" / "paper_assets_20260608" / "targeted_masked_error_audit_yield_review_results_final_20260612.json"
RAW_AUDIO_DIR = ROOT / "mvp_eval" / "audio" / "raw"
CONFIG_PATH = ROOT / "xiaomi_api_config.json"

WINDOW_SECONDS = 6.0
ROW_SLEEP_SECONDS = 0.4

REFUSAL_MARKERS = [
    "抱歉",
    "无法处理",
    "不能处理",
    "无法转写",
    "不能转写",
    "没有听到",
    "无法识别",
]


def norm(text: object) -> str:
    s = str(text or "").lower()
    for ch in " \t\r\n，。！？、；：,.!?;:（）()[]【】「」『』《》“”\"'`·":
        s = s.replace(ch, "")
    return s


def run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.stdout.strip()


def audio_duration(path: Path) -> float:
    out = run([
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=nw=1:nk=1",
        str(path),
    ])
    return float(out)


def cut_audio(src: Path, dst: Path, start: float, dur: float) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(src),
            "-ss",
            f"{start:.3f}",
            "-t",
            f"{dur:.3f}",
            "-acodec",
            "pcm_s16le",
            str(dst),
        ],
        check=True,
    )


def read_rows() -> list[dict]:
    data = json.loads(INPUT_JSON.read_text(encoding="utf-8"))
    rows = [r for r in data["rows"] if r.get("final_audit_outcome") == "confirmed masked"]
    rows.sort(key=lambda r: int(str(r["probe_candidate_id"]).split("_")[-1]))
    return rows


def parse_negative_readings(row: dict) -> list[str]:
    vals: list[str] = []
    actual = str(row.get("raw_tts_actual_reading") or "").strip()
    if actual:
        vals.append(actual)
    target = str(row.get("target_span") or "").strip()
    for line in str(row.get("risk_span_lines") or "").splitlines():
        if target and not line.startswith(target + "=>"):
            continue
        m = re.search(r"\|wrong:([^\n]+)", line)
        if m:
            vals.extend(x.strip() for x in re.split(r"[/,，;；]", m.group(1)) if x.strip())
    # Common ASR renderings for hyphenated spans.
    if "-" in target:
        parts = [p for p in target.split("-") if p]
        if len(parts) >= 2:
            vals.extend([
                "至".join(parts),
                "到".join(parts),
                "负".join(parts),
                "减".join(parts),
            ])
    out = []
    seen = set()
    for v in vals:
        nv = norm(v)
        if nv and nv not in seen:
            seen.add(nv)
            out.append(v)
    return out


def find_audio(case_id: str) -> Path:
    p = RAW_AUDIO_DIR / f"{case_id}.wav"
    if p.exists():
        return p
    matches = list((ROOT / "mvp_eval").glob(f"**/raw/{case_id}.wav"))
    if matches:
        return matches[0]
    raise FileNotFoundError(f"missing raw audio for {case_id}")


def build_manifest(window_seconds: float) -> list[dict]:
    rows = read_rows()
    audio_dir = OUT_DIR / f"audio_span_iso_{int(window_seconds)}s"
    manifest = []
    for row in rows:
        case_id = str(row["case_id"])
        pid = str(row["probe_candidate_id"])
        target = str(row.get("target_span") or "")
        raw_text = str(row.get("raw_text") or "")
        audio_path = find_audio(case_id)
        duration = audio_duration(audio_path)
        idx = raw_text.find(target) if target else -1
        if idx < 0:
            center_ratio = 0.5
            occurrence_count = 0
        else:
            center_ratio = (idx + max(1, len(target)) / 2) / max(1, len(raw_text))
            occurrence_count = raw_text.count(target)
        center = max(0.0, min(duration, center_ratio * duration))
        start = max(0.0, center - window_seconds / 2)
        end = min(duration, center + window_seconds / 2)
        if end - start < window_seconds and duration >= window_seconds:
            if start <= 0.001:
                end = min(duration, window_seconds)
            elif end >= duration - 0.001:
                start = max(0.0, duration - window_seconds)
        safe_target = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff._-]+", "_", target or "target")
        clip = audio_dir / f"{pid}_{case_id}_{safe_target}_iso{int(window_seconds)}s.wav"
        cut_audio(audio_path, clip, start, end - start)
        manifest.append({
            "probe_candidate_id": pid,
            "case_id": case_id,
            "freeze_id": row.get("freeze_id"),
            "primary_type": row.get("primary_type"),
            "cdrd_label": row.get("cdrd_label"),
            "target_span": target,
            "expected_reading": row.get("expected_reading"),
            "raw_tts_actual_reading": row.get("raw_tts_actual_reading"),
            "negative_readings": parse_negative_readings(row),
            "raw_text_len": len(raw_text),
            "target_first_char_index": idx,
            "target_occurrence_count": occurrence_count,
            "source_audio_path": str(audio_path),
            "source_audio_duration_seconds": round(duration, 3),
            "span_center_seconds_est": round(center, 3),
            "clip_start_seconds": round(start, 3),
            "clip_end_seconds": round(end, 3),
            "clip_duration_seconds": round(end - start, 3),
            "clip_audio_path": str(clip),
            "full_asr_source": row.get("raw_asr_display_source"),
            "full_asr_text": row.get("raw_asr_display_text"),
            "full_default_asr_text": row.get("raw_default_asr_text"),
            "full_omni_strict_asr_text": row.get("raw_omni_strict_asr_text"),
            "asr_masking_evidence": row.get("asr_masking_evidence"),
        })
    return manifest


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def find_api_key() -> str | None:
    for name in ["MIMO_API_KEY", "XIAOMI_MIMO_API_KEY"]:
        val = os.environ.get(name)
        if val:
            return val
    return None


def call_mimo_asr(clip: Path) -> tuple[str, dict]:
    key = find_api_key()
    if not key:
        raise RuntimeError("MIMO_API_KEY or XIAOMI_MIMO_API_KEY must be set in the environment")
    os.environ["MIMO_API_KEY"] = key
    sys.path.insert(0, str(ROOT))
    from run_xiaomi_tts_asr_eval import call_asr  # noqa: PLC0415

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    config["api_key_env"] = "MIMO_API_KEY"
    config["request_timeout_seconds"] = int(os.environ.get("SPAN_ISO_ASR_TIMEOUT_SECONDS", "180"))
    text, response = call_asr(config, clip)
    return str(text or ""), response


def classify(row: dict, asr_text: str) -> tuple[str, dict]:
    ntext = norm(asr_text)
    if not ntext or any(marker in asr_text for marker in REFUSAL_MARKERS):
        return "no_output", {"matched_expected": False, "matched_surface": False, "matched_negative": []}

    expected = norm(row.get("expected_reading"))
    surface = norm(row.get("target_span"))
    negatives = [(v, norm(v)) for v in row.get("negative_readings") or [] if norm(v)]

    matched_expected = bool(expected and expected in ntext)
    matched_surface = bool(surface and surface in ntext)
    matched_negative = [v for v, nv in negatives if nv and nv in ntext]

    masked = matched_expected or matched_surface
    exposed = bool(matched_negative)
    if masked and exposed:
        label = "mixed_masked_and_exposed"
    elif masked:
        label = "still_masked"
    elif exposed:
        label = "exposed"
    else:
        label = "other_transcript"
    return label, {
        "matched_expected": matched_expected,
        "matched_surface": matched_surface,
        "matched_negative": matched_negative,
    }


def run_asr(
    manifest: list[dict],
    window_seconds: float,
    limit: int | None = None,
    output_tag: str | None = None,
) -> list[dict]:
    tag = output_tag or f"span_iso_{int(window_seconds)}s"
    out_path = OUT_DIR / "outputs" / f"mimo_strict_{tag}_results.jsonl"
    existing = load_jsonl(out_path)
    by_id = {r["probe_candidate_id"]: r for r in existing if not r.get("error")}
    rows = existing[:]
    todo = manifest[:limit] if limit else manifest
    for i, item in enumerate(todo, 1):
        pid = item["probe_candidate_id"]
        if pid in by_id:
            print(f"[{i}/{len(todo)}] {pid} skipped")
            continue
        started = time.time()
        error = ""
        text = ""
        response = None
        try:
            text, response = call_mimo_asr(Path(item["clip_audio_path"]))
        except Exception as exc:  # keep resumable output
            error = repr(exc)
        label, evidence = classify(item, text)
        rec = {
            **item,
            "isolated_asr_model": "mimo-v2.5",
            "isolated_asr_protocol": "strict_prompt",
            "isolated_asr_text": text,
            "isolated_asr_label": label if not error else "error",
            "isolated_asr_match_json": json.dumps(evidence, ensure_ascii=False),
            "latency_seconds": round(time.time() - started, 3),
            "error": error,
            "asr_response_json": json.dumps(response, ensure_ascii=False)[:2000] if response else "",
        }
        rows.append(rec)
        write_jsonl(out_path, rows)
        print(f"[{i}/{len(todo)}] {pid} {label if not error else 'error'} {round(time.time() - started, 1)}s")
        if ROW_SLEEP_SECONDS:
            time.sleep(ROW_SLEEP_SECONDS)
    return load_jsonl(out_path)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = []
    for row in rows:
        for k in row:
            if k not in keys and k != "asr_response_json":
                keys.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in keys})


def summarize(rows: list[dict], window_seconds: float) -> str:
    completed = [r for r in rows if not r.get("error")]
    by_label = Counter(r.get("isolated_asr_label") or "missing" for r in rows)
    by_type: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        by_type[str(r.get("primary_type") or "")][r.get("isolated_asr_label") or "missing"] += 1

    order = ["exposed", "still_masked", "mixed_masked_and_exposed", "other_transcript", "no_output", "error"]
    lines = [
        "# Span-Isolated ASR Probe Summary (2026-06-12)",
        "",
        "## Setup",
        "",
        f"- Input: 46 MiMo confirmed masked cases from the final 110-row targeted audit.",
        f"- Audio: MiMo Raw full utterances, cut into estimated risk-span clips.",
        f"- Clip window: {window_seconds:.1f} seconds centered by target string position in `raw_text`.",
        "- ASR: MiMo v2.5 strict prompt.",
        "- This is a first-pass diagnostic. Clip boundaries are approximate and should be refined with forced alignment if the result is used as a main paper claim.",
        "",
        "## Overall",
        "",
        "| isolated ASR outcome | count |",
        "|---|---:|",
    ]
    for key in order:
        lines.append(f"| {key} | {by_label.get(key, 0)} |")
    lines.extend([
        f"| total rows written | {len(rows)} |",
        f"| completed without API error | {len(completed)} |",
        "",
        "Definitions:",
        "",
        "- `exposed`: isolated ASR contains a known wrong/raw reading and does not contain the expected or surface-correct form.",
        "- `still_masked`: isolated ASR contains the expected reading or original surface span and does not contain a known wrong/raw reading.",
        "- `mixed_masked_and_exposed`: isolated ASR contains both surface-correct and wrong-reading evidence.",
        "- `other_transcript`: non-empty transcript without expected/surface or known wrong-reading match.",
        "- `no_output`: empty/refusal/unusable transcript.",
        "",
        "## By Primary Type",
        "",
        "| primary_type | total | exposed | still_masked | mixed | other | no_output | error |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for typ in sorted(by_type):
        c = by_type[typ]
        total = sum(c.values())
        lines.append(
            f"| {typ} | {total} | {c.get('exposed', 0)} | {c.get('still_masked', 0)} | "
            f"{c.get('mixed_masked_and_exposed', 0)} | {c.get('other_transcript', 0)} | "
            f"{c.get('no_output', 0)} | {c.get('error', 0)} |"
        )
    lines.extend([
        "",
        "## Files",
        "",
        f"- Manifest: `{OUT_DIR / f'manifest_span_iso_{int(window_seconds)}s_46.jsonl'}`",
        f"- Clips: `{OUT_DIR / f'audio_span_iso_{int(window_seconds)}s'}`",
        f"- JSONL results: `{OUT_DIR / 'outputs' / f'mimo_strict_span_iso_{int(window_seconds)}s_results.jsonl'}`",
        f"- CSV results: `{OUT_DIR / 'outputs' / f'mimo_strict_span_iso_{int(window_seconds)}s_results.csv'}`",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--window-seconds", type=float, default=WINDOW_SECONDS)
    parser.add_argument("--skip-asr", action="store_true")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--manifest-path", type=Path, default=None)
    parser.add_argument("--output-tag", type=str, default=None)
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.manifest_path:
        manifest = load_jsonl(args.manifest_path)
        manifest_path = args.manifest_path
        print(f"loaded manifest rows={len(manifest)} path={manifest_path}")
    else:
        manifest = build_manifest(args.window_seconds)
        manifest_path = OUT_DIR / f"manifest_span_iso_{int(args.window_seconds)}s_46.jsonl"
        write_jsonl(manifest_path, manifest)
        print(f"manifest rows={len(manifest)} path={manifest_path}")

    if args.skip_asr:
        return

    rows = run_asr(manifest, args.window_seconds, args.limit, args.output_tag)
    tag = args.output_tag or f"span_iso_{int(args.window_seconds)}s"
    csv_path = OUT_DIR / "outputs" / f"mimo_strict_{tag}_results.csv"
    write_csv(csv_path, rows)
    summary = summarize(rows, args.window_seconds)
    summary_path = OUT_DIR / f"span_isolated_asr_probe_summary_iso{int(args.window_seconds)}s_20260612.md"
    summary_path.write_text(summary, encoding="utf-8")
    print(f"summary={summary_path}")


if __name__ == "__main__":
    main()
