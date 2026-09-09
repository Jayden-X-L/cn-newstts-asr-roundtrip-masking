#!/usr/bin/env python3
"""Verify the local revision supplement without private paths or dependencies."""

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main():
    for item in load("file_manifest.json"):
        path = ROOT / item["path"]
        assert path.stat().st_size == item["size"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
    rows = load("paired_records_46.json")
    selected = [r for r in rows if r["effective_context_reduction"]]
    assert len(rows) == 46 and len(selected) == 44
    matrix = [[sum(r["full_label"] == s and r["selected_clip_label"] == t for r in selected) for t in "SWO"] for s in "SWO"]
    assert matrix == [[8, 11, 0], [0, 22, 2], [0, 0, 1]]
    b = sum(r["full_label"] == "S" and r["selected_clip_label"] != "S" for r in selected)
    c = sum(r["full_label"] != "S" and r["selected_clip_label"] == "S" for r in selected)
    p = min(1.0, 2 * sum(math.comb(b + c, k) for k in range(min(b, c) + 1)) / 2**(b + c))
    assert p == 0.0009765625
    integrity = load("integrity_records_46.json")
    assert len(integrity) == 46 and all(r["latest_aa_verdict"] == r["latest_bb_verdict"] == "passed" for r in integrity)
    for r in rows:
        if r["selected_audio_version"] == "repaired_r1":
            audio = ROOT / "audio" / f"{r['review_id']}_repaired_r1.wav"
            assert hashlib.sha256(audio.read_bytes()).hexdigest() == r["selected_clip_sha256"]
        if not r["effective_context_reduction"]:
            assert r["raw_sha256"] == r["selected_clip_sha256"] and r["full_transcript"] == r["selected_clip_transcript"]
    controls = load("reproducibility_controls_8.json")
    assert len(controls) == 8 and all(r["baseline_transcript"] == r["rerun_transcript"] for r in controls)
    outputs = {r["item_id"]: r for r in load("qwen_outputs_12.json")}
    assert len(outputs) == 12 and all(not r["error"] for r in outputs.values())
    for r in rows:
        if r["selected_audio_version"] == "repaired_r1":
            new = outputs[r["review_id"] + "_repaired_r1"]
            assert new["asr_text"] == r["selected_clip_transcript"]
            assert new["input_sha256"] == r["selected_clip_sha256"]
    print(json.dumps({"status": "PASS", "pairs": 44, "matrix_S_W_O": matrix, "p": p, "control_matches": 8}, indent=2))


if __name__ == "__main__":
    main()
