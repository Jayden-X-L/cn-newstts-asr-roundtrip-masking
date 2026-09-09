#!/usr/bin/env python3
"""Offline verification of the Qwen paired and MiMo descriptive supplements."""

import hashlib
import json
import runpy
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main():
    if not __debug__:
        raise RuntimeError("Do not use -O: input verification requires assertions")
    checker = runpy.run_path(str(ROOT / "verify_tables.py"))
    checker["verify"](ROOT)
    runpy.run_path(str(ROOT / "verify_qwen.py"), run_name="__main__")
    rows = load("mimo/selected_records_46.json")
    outputs = {r["review_id"]: r for r in load("mimo/outputs_4.json")}
    inputs = {r["review_id"]: r for r in load("mimo/comparison_4.json")}
    accepted = {r["review_id"]: r for r in load("integrity_records_46.json")}
    qwen = {r["review_id"]: r for r in load("paired_records_46.json")}
    stats = load("mimo/diagnostic_statistics.json")
    assert len(rows) == len({r["review_id"] for r in rows}) == 46
    assert len(outputs) == 4 and set(outputs) == {"B001", "B013", "B014", "B017"}
    assert all(not r["error"] and r["http_attempts"] == 1 for r in outputs.values())
    effective = [r for r in rows if r["effective_context_reduction"]]
    identities = [r for r in rows if r["is_identical_to_full_recording"]]
    historical = [r for r in rows if r["result_origin"] == "historical_aligned_20260612"]
    assert len(effective) == 44 and len(historical) == 42
    assert {r["review_id"] for r in identities} == {"B001", "B014"}
    assert sum(r["result_origin"] == "repaired_rerun_20260909" for r in effective) == 2
    for r in rows:
        rid = r["review_id"]
        assert r["audio_sha256"] == accepted[rid]["selected_clip_sha256"]
        assert r["interval_seconds"] == accepted[rid]["selected_interval_seconds"]
        if rid in outputs:
            out, item = outputs[rid], inputs[rid]
            assert out["audio_sha256"] == r["audio_sha256"] == item["selected_clip_sha256"]
            assert out["asr_text"] == r["selected_transcript"] == item["new_transcript"]
            assert r["selected_label"] == item["selected_label"]
            audio = ROOT / "audio" / f"{rid}_repaired_r1.wav"
            assert hashlib.sha256(audio.read_bytes()).hexdigest() == r["audio_sha256"]
        else:
            assert r["selected_transcript"] == r["historical_clip_transcript"]
            assert r["selected_label"] == r["historical_clip_label"]
        if r in identities:
            assert r["selected_label"] == "still_masked"
            assert qwen[rid]["selected_clip_label"] == "W"
    labels = Counter(r["selected_label"] for r in effective)
    assert labels == {"exposed": 16, "still_masked": 13, "no_output": 12, "other_transcript": 3}
    populations = {"effective_44_mixed_date_descriptive": effective,
                   "all_46_mixed_date_descriptive": rows,
                   "identity_2_descriptive": identities,
                   "unchanged_42_historical": historical}
    for name, population in populations.items():
        counts = Counter(r["selected_label"] for r in population)
        assert stats[name]["n"] == len(population)
        assert all(counts[k] == v for k, v in stats[name]["labels"].items())
    assert all(r["result_origin"] == "historical_aligned_20260612" for r in effective if r["selected_label"] == "exposed")
    assessment = load("mimo/transcript_assessments.json")
    assert len(assessment) == 1 and assessment[0]["review_id"] == "B017"
    assert assessment[0]["audio_sha256"] == outputs["B017"]["audio_sha256"]
    assert assessment[0]["asr_text"] == outputs["B017"]["asr_text"]
    assert assessment[0]["selected_label"] == "other_transcript"
    assert assessment[0]["human_relabel"] is False and assessment[0]["author_confirmation"] is False
    assert qwen["B017"]["selected_clip_label"] == "W"
    protocol = load("mimo/protocol.json")
    assert protocol["asr"]["body_template"]["model"] == "mimo-v2.5"
    assert protocol["asr"]["body_template"]["temperature"] == 0
    assert protocol["asr"]["body_template"]["max_completion_tokens"] == 2048
    assert protocol["request_timeout_seconds"] == 180
    assert all(r["requested_model"] == r["response_model"] == "mimo-v2.5" for r in outputs.values())
    assert load("mimo/environment.json")["historical_backend_revision_available"] is False
    assert stats["not_a_protocol_matched_paired_test"] is True
    assert len(load("mimo/http_attempts.json")) == 4
    assert load("mimo/completion.json")["no_content_based_retries"] is True
    print(json.dumps({"status": "PASS", "mimo_effective_n": 44, "mimo_labels": dict(labels),
        "mimo_rerun_inputs": 4, "mimo_effective_reruns": 2, "historical_outputs_retained": 42,
        "qwen_B017": "W", "mimo_B017": "other_transcript", "new_blind_human_labels": 0}, indent=2))


if __name__ == "__main__":
    main()
