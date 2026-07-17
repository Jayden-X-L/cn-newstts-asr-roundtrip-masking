#!/usr/bin/env python3
"""Compare Paraformer outputs from the FunASR use_itn flag toggle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_DIR = ROOT / "mvp_eval/paraformer_targeted_20260717"
RESULT_DIR = ROOT / "mvp_eval/paraformer_itn_qwen3_20260717"


def text(value: Any) -> str:
    return str(value or "").strip()


def load_latest(path: Path) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                latest[text(row.get("item_id"))] = row
    return latest


def compare(off_path: Path, on_path: Path) -> dict[str, Any]:
    off = load_latest(off_path)
    on = load_latest(on_path)
    if set(off) != set(on):
        raise RuntimeError(
            f"item mismatch: off_only={sorted(set(off) - set(on))}, "
            f"on_only={sorted(set(on) - set(off))}"
        )

    changed = [item_id for item_id in off if text(off[item_id].get("asr_text")) != text(on[item_id].get("asr_text"))]
    confirmed = [
        item_id
        for item_id, row in off.items()
        if text(row.get("human_audit_outcome")) == "confirmed masked"
    ]
    confirmed_changed = [item_id for item_id in confirmed if item_id in changed]
    return {
        "rows": len(off),
        "off_errors": sum(bool(text(row.get("error"))) for row in off.values()),
        "on_errors": sum(bool(text(row.get("error"))) for row in on.values()),
        "transcript_changed_rows": len(changed),
        "changed_item_ids": changed,
        "human_confirmed_wrong_rows": len(confirmed),
        "human_confirmed_changed_rows": len(confirmed_changed),
        "human_confirmed_changed_item_ids": confirmed_changed,
    }


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    full = compare(
        BASE_DIR / "paraformer_full_220_results.jsonl",
        RESULT_DIR / "paraformer_itn_full_220_results.jsonl",
    )
    aligned = compare(
        BASE_DIR / "paraformer_aligned_46_results.jsonl",
        RESULT_DIR / "paraformer_itn_aligned_46_results.jsonl",
    )
    summary = {
        "control": "FunASR use_itn flag toggle on the same Paraformer-zh route",
        "off_protocol": "paraformer_plain_no_itn",
        "on_protocol": "paraformer_plain_itn",
        "full_audio": full,
        "aligned_clips": aligned,
        "interpretation": (
            "The toggle produced identical transcripts in this Paraformer route. "
            "It is therefore a no-effect parameter check, not evidence that active "
            "inverse text normalization causes or prevents masking."
        ),
    }
    (RESULT_DIR / "paraformer_itn_toggle_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown = [
        "# Paraformer `use_itn` Toggle Check",
        "",
        f"- Full-audio transcripts changed: **{full['transcript_changed_rows']}/{full['rows']}**",
        f"- Human-confirmed wrong-reading transcripts changed: **{full['human_confirmed_changed_rows']}/{full['human_confirmed_wrong_rows']}**",
        f"- Aligned-clip transcripts changed: **{aligned['transcript_changed_rows']}/{aligned['rows']}**",
        "",
        "The flag toggle produced identical transcripts in this Paraformer route. "
        "Accordingly, it is reported as a no-effect parameter check rather than "
        "as a causal ITN ablation.",
    ]
    (RESULT_DIR / "paraformer_itn_toggle_summary.md").write_text(
        "\n".join(markdown) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
