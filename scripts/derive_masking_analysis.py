"""Recompute revision analyses from public files using Python's standard library.

No listening labels are generated or changed. Optional archive verification reads
WAV bytes without extracting the ZIP; the default checks the published inventory.
"""

import argparse
import csv
import hashlib
import json
import re
import unicodedata
import zipfile
from collections import Counter
from contextlib import nullcontext
from pathlib import Path

import masking_revision_rules as rules

INPUTS = {
    "frozen": "metadata/frozen_benchmark/p1p2_frozen_200_cases.csv",
    "primary": "labels/targeted_audit_110/targeted_masked_error_audit_yield_review_results_final_20260612.csv",
    "cosy": "labels/cosyvoice_110/cosyvoice_raw_110_human_review_labels_final_20260614.csv",
    "blind": "results/paper_tables/paper_assets_20260608/targeted_audit_110_blind_relabel_30_agreement_20260620.csv",
    "qwen": "results/qwen3_asr/qwen3_confirmed_97_transcript_audit.csv",
    "clips": "results/qwen3_asr/qwen3_aligned_46_transcript_audit.csv",
    "paraformer": "results/paraformer/paraformer_confirmed_97_transcript_audit.csv",
    "real": "metadata/candidate_pools/cn_newstts_real_500_texts.jsonl",
    "synthetic": "metadata/candidate_pools/cn_newstts_synth_5k.jsonl",
    "prior_dev": "metadata/prior_work/cn_news_tts_bench_v0.1/dev.jsonl",
    "prior_test": "metadata/prior_work/cn_news_tts_bench_v0.1/test_public.jsonl",
    "prior_manifest": "metadata/prior_work/cn_news_tts_bench_v0.1/manifest.json",
    "audio_inventory": "metadata/audio_inventory/mimo_raw_200.csv",
    "audio_manifest": "metadata/audio_inventory/manifest.json",
}
RESULT_FILES = (
    "sample_flow_200_to_110.csv", "prior_work_comparison.json",
    "blind_label_sensitivity.csv", "variant_scope_audit_97.csv",
    "qwen_paired_transition_matrix.csv", "masking_only_results.json",
)
MASKED = "confirmed masked"
SURFACE = "exact_surface_correct_recovery"
WRONG = "wrong_or_noncanonical_form_preserved"
OTHER = "other_no_exact_surface_recovery"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest_stream(handle):
    h = hashlib.sha256()
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        h.update(block)
    return h.hexdigest()


def sha256(path):
    with path.open("rb") as handle:
        return digest_stream(handle)


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def text_norm(value):
    return "".join(c for c in unicodedata.normalize("NFKC", value).lower()
                   if not c.isspace() and not unicodedata.category(c).startswith("P"))


def compact(value):
    return "".join(str(value).split())


def score_relation_check(target, expected, heard):
    match = re.fullmatch(r"(\d{1,3})[-:：](\d{1,3})", compact(target))
    if not match:
        return False, "outside_two_number_score_scope"
    left, right = map(int, match.groups())
    left_forms = {str(left), rules.num_zh(left), rules.digit_zh(str(left))}
    right_forms = {str(right), rules.num_zh(right), rules.digit_zh(str(right))}
    intended = {f"{a}比{b}" for a in left_forms for b in right_forms}
    negatives = {f"{a}{op}{b}" for a in left_forms for b in right_forms for op in "至到减负"}
    if compact(expected) not in intended:
        return False, "expected_reading_not_an_unambiguous_score_relation"
    if compact(heard) not in negatives:
        return False, "heard_annotation_not_an_explicit_value_preserving_relation_error"
    return True, "score_relation_changed_with_operands_preserved"


def tts_key(row):
    names = {"MiMo-V2.5-TTS API": "MiMo", "CosyVoice-300M-SFT": "CosyVoice"}
    require(row["tts_system"] in names, f"Unknown TTS system: {row['tts_system']}")
    return names[row["tts_system"]]


def verify_audio(paths, frozen, archive=None, audio_root=None):
    inventory = read_csv(paths["audio_inventory"])
    manifest = json.loads(paths["audio_manifest"].read_text())
    require(sha256(paths["audio_inventory"]) == manifest["inventory_sha256"], "Audio inventory hash mismatch")
    require(len(inventory) == len(frozen) == 200, "Expected 200 frozen recordings")
    require({r["case_id"] for r in inventory} == {r["case_id"] for r in frozen}, "Audio inventory IDs differ")
    require(all(int(r["bytes"]) > 44 and re.fullmatch(r"[0-9a-f]{64}", r["sha256"])
                for r in inventory), "Invalid audio inventory entry")
    verification = {"mode": "inventory_only", "inventory_entries": 200, "verified_audio_files": 0,
                    "note": "Availability is recorded in the published inventory; no audio bytes were read."}
    if archive:
        require(archive.stat().st_size == manifest["archive_bytes"], "Zenodo ZIP size mismatch")
        require(sha256(archive) == manifest["archive_sha256"], "Zenodo ZIP SHA-256 mismatch")
    if archive or audio_root:
        with zipfile.ZipFile(archive) if archive else nullcontext(None) as z:
            for row in inventory:
                if z:
                    matches = [n for n in z.namelist() if n == row["archive_path"]
                               or n.endswith("/" + row["archive_path"])]
                    require(len(matches) == 1, f"Missing or ambiguous WAV: {row['case_id']}")
                    require(z.getinfo(matches[0]).file_size == int(row["bytes"]), "WAV size mismatch")
                    with z.open(matches[0]) as handle:
                        digest = digest_stream(handle)
                else:
                    wav = audio_root / f"{row['case_id']}.wav"
                    require(wav.is_file(), f"Missing WAV: {wav.name}")
                    require(wav.stat().st_size == int(row["bytes"]), f"WAV size mismatch: {wav.name}")
                    digest = sha256(wav)
                require(digest == row["sha256"], f"WAV SHA-256 mismatch: {row['case_id']}")
        verification = {"mode": "zenodo_zip" if archive else "audio_directory",
                        "inventory_entries": 200, "verified_audio_files": 200,
                        "note": "All 200 Raw WAV sizes and SHA-256 digests verified against the inventory."}
        if archive:
            verification["archive_sha256"] = manifest["archive_sha256"]
    return {r["case_id"] for r in inventory}, verification


def derive(root, out, archive=None, audio_root=None):
    paths = {key: root / name for key, name in INPUTS.items()}
    for name, path in paths.items():
        require(path.is_file(), f"Missing public input ({name}): {INPUTS[name]}")
    tables = {k: read_csv(paths[k]) for k in ("frozen", "primary", "cosy", "blind", "qwen", "clips", "paraformer")}
    frozen, primary, cosy, blind, qwen, clips, paraformer = (tables[k] for k in tables)
    audio_ids, verification = verify_audio(paths, frozen, archive, audio_root)
    for name, table in (("frozen", frozen), ("primary", primary), ("cosy", cosy), ("blind", blind), ("clips", clips)):
        key = "probe_candidate_id" if name == "clips" else "case_id"
        require(len({r[key] for r in table}) == len(table), f"Duplicate IDs in {name}")
    selected = {r["case_id"] for r in primary}
    require(len(primary) == len(cosy) == 110 and selected == {r["case_id"] for r in cosy}, "TTS audit pools differ")
    flow = []
    for row in frozen:
        matched = rules.classify_case(row)[0]
        available = row["case_id"] in audio_ids
        included = row["case_id"] in selected
        require(included == bool(matched and available), f"Rule-selection mismatch: {row['case_id']}")
        flow.append({"case_id": row["case_id"], "source": row["source"],
                     "matched_rule_families": ";".join(matched), "raw_audio_available": available,
                     "included": included, "exclusion_reason": "" if included else "no_audit_rule_match"})

    prior_manifest = json.loads(paths["prior_manifest"].read_text())
    prior_hashes = {name: sha256(paths[key]) for name, key in (("dev", "prior_dev"), ("test_public", "prior_test"))}
    require(prior_hashes == prior_manifest["sha256"], "Pinned prior benchmark hash mismatch")
    prior_rows = read_jsonl(paths["prior_dev"]) + read_jsonl(paths["prior_test"])
    prior_texts = {text_norm(row["text"]) for row in prior_rows}
    candidates = read_jsonl(paths["real"]) + read_jsonl(paths["synthetic"])
    require(len(prior_rows) == 1000 and len(candidates) == 5500, "Unexpected text-pool size")
    overlap = {"prior_release": prior_manifest["release"], "prior_commit": prior_manifest["commit"],
               "prior_data_sha256": prior_hashes, "prior_records": len(prior_rows),
               "current_frozen_records": len(frozen),
               "frozen_normalized_full_text_matches": sum(text_norm(r["raw_text"]) in prior_texts for r in frozen),
               "current_candidate_records": len(candidates),
               "candidate_normalized_full_text_matches": sum(text_norm(r["raw_text"]) in prior_texts for r in candidates),
               "comparison": "NFKC, lowercase, remove Unicode punctuation and whitespace; full-text equality only",
               "shared_elements": "Reading-risk motifs, expected/negative reading annotations, and transcript pattern matching",
               "different_experimental_evidence": "The cited v1 paper reports a seven-product automatic leaderboard; this manuscript reports audio-first labels, route-union masking, and full-to-clip diagnostics."}

    base = Counter(r["public_audit_outcome"] for r in primary)
    replace, drop = base.copy(), base.copy()
    primary_by_id = {r["case_id"]: r for r in primary}
    for row in blind:
        require(primary_by_id[row["case_id"]]["public_audit_outcome"] == row["original_label"], "Blind baseline mismatch")
        replace[row["original_label"]] -= 1
        replace[row["blind_label"]] += 1
        if row["original_label"] != row["blind_label"]:
            drop[row["original_label"]] -= 1

    def scenario(name, counts):
        return {"scenario": name, "n": sum(counts.values()), "masked": counts[MASKED],
                "exposed": counts["exposed TTS error"], "no_error": counts["no Raw TTS error"],
                "unresolved": counts["uncertain"] + counts["not judgeable"]}

    sensitivity = [scenario("MiMo frozen primary", base),
                   scenario("MiMo replace 30 blind-subset labels", replace),
                   scenario("MiMo exclude 7 discordant cases", drop)]
    variants = []
    for system, rows, outcome, target, expected, heard in [
        ("MiMo", primary, "public_audit_outcome", "target_span", "expected_reading", "raw_tts_actual_reading"),
        ("CosyVoice", cosy, "cosyvoice_outcome", "target_span_review", "expected_reading_review", "cosyvoice_heard_reading"),
    ]:
        for row in rows:
            if row[outcome] != MASKED:
                continue
            keep, reason = score_relation_check(row[target], row[expected], row[heard])
            if not keep:
                if re.search(r"(?:F-|B-|伊尔|运-|737-)", row[target]):
                    reason = "model_reading_conventions_excluded_from_restricted_check"
                elif re.search(r"[A-Za-z]", row[target]):
                    reason = "unit_or_membership_reading_conventions_excluded_from_restricted_check"
                elif re.search(r"20\d\d", row[target]):
                    reason = "year_reading_conventions_excluded_from_restricted_check"
            variants.append({"tts": system, "probe_candidate_id": row["probe_candidate_id"],
                             "case_id": row["case_id"], "primary_label": row[outcome],
                             "target": row[target], "expected_record": row[expected], "heard_record": row[heard],
                             "retained_in_restricted_score_check": keep, "reason": reason,
                             "interpretation": "Derived from saved listening notes; exclusion does not relabel a file as correct."})
    kept = {(r["tts"], r["probe_candidate_id"]) for r in variants if r["retained_in_restricted_score_check"]}
    full_by_id = {r["probe_candidate_id"]: r for r in qwen if tts_key(r) == "MiMo"}
    require(len(qwen) == len(paraformer) == 97, "Expected 97 ASR-control files")
    expected_keys = {(r["tts"], r["probe_candidate_id"]) for r in variants}
    for table in (qwen, paraformer):
        require({(tts_key(r), r["probe_candidate_id"]) for r in table} == expected_keys, "ASR control IDs differ from masked files")
    require(len(clips) == len(full_by_id) == 46 and {r["probe_candidate_id"] for r in clips} == set(full_by_id), "Unpaired clips")
    transitions = Counter((full_by_id[r["probe_candidate_id"]]["reviewed_qwen_relation"], r["reviewed_qwen_relation"]) for r in clips)
    transition_rows = [{"full_outcome": a, "clip_outcome": b, "count": transitions[(a, b)]}
                       for a in (SURFACE, WRONG, OTHER) for b in (SURFACE, WRONG, OTHER)]
    require(sum(r["count"] for r in transition_rows) == 46, "Unknown Qwen outcome")
    restricted_asr = {}
    for name, rows, label in [("Qwen3-ASR", qwen, "reviewed_qwen_relation"),
                              ("Paraformer", paraformer, "reviewed_paraformer_relation")]:
        subset = [r for r in rows if (tts_key(r), r["probe_candidate_id"]) in kept]
        restricted_asr[name] = {"n": len(subset), "surface": sum(r[label] == SURFACE for r in subset),
                                "outcomes": dict(Counter(r[label] for r in subset))}
    restricted_pairs = [r for r in clips if ("MiMo", r["probe_candidate_id"]) in kept]
    restricted_transitions = Counter((full_by_id[r["probe_candidate_id"]]["reviewed_qwen_relation"], r["reviewed_qwen_relation"]) for r in restricted_pairs)
    mi = {r["case_id"] for r in primary if r["public_audit_outcome"] == MASKED}
    co = {r["case_id"] for r in cosy if r["cosyvoice_outcome"] == MASKED}
    summary = {"sample_flow": {"frozen": len(frozen), "included": len(selected),
                               "included_sources": dict(Counter(r["source"] for r in flow if r["included"])),
                               "excluded_sources": dict(Counter(r["source"] for r in flow if not r["included"])),
                               "raw_audio_available": len(audio_ids)},
               "prior_work": overlap, "blind_sensitivity": sensitivity,
               "variant_scope": {"n_primary_masked_files": len(variants),
                                   "retained_by_tts": dict(Counter(r["tts"] for r in variants if r["retained_in_restricted_score_check"])),
                                   "excluded_from_restricted_check": len(variants) - len(kept),
                                   "restricted_asr": restricted_asr,
                                   "restricted_qwen_transitions": {f"{a} -> {b}": n for (a, b), n in restricted_transitions.items()}},
               "masked_case_id_overlap": {"both": len(mi & co), "mimo_only": len(mi - co), "cosyvoice_only": len(co - mi)},
               "qwen_paired_transitions": transition_rows}
    out.mkdir(parents=True, exist_ok=True)
    for name, rows in [("sample_flow_200_to_110.csv", flow), ("blind_label_sensitivity.csv", sensitivity),
                       ("variant_scope_audit_97.csv", variants), ("qwen_paired_transition_matrix.csv", transition_rows)]:
        write_csv(out / name, rows)
    write_json(out / "prior_work_comparison.json", overlap)
    write_json(out / "masking_only_results.json", summary)
    write_json(out / "audio_verification.json", verification)
    write_csv(out / "input_checksums.csv", [{"repository_relative_path": name, "bytes": (root / name).stat().st_size,
                                            "sha256": sha256(root / name)} for name in INPUTS.values()])
    return summary, verification


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for generated tables and provenance")
    parser.add_argument("--check", action="store_true", help="Compare six derived tables against results/masking_revision")
    audio = parser.add_mutually_exclusive_group()
    audio.add_argument("--zenodo-zip", type=Path, help="Verify original Zenodo ZIP and all 200 Raw WAV digests")
    audio.add_argument("--audio-root", type=Path, help="Extracted audio/mimo_v25_tts_p1p2_200/raw directory")
    args = parser.parse_args()
    reference = (args.data_root / "results/masking_revision").resolve()
    require(not args.check or args.output_dir.resolve() != reference, "--check output must not overwrite its reference")
    summary, verification = derive(args.data_root, args.output_dir, args.zenodo_zip, args.audio_root)
    if args.check:
        for name in RESULT_FILES:
            reader = read_csv if name.endswith(".csv") else lambda p: json.loads(p.read_text(encoding="utf-8"))
            require(reader(reference / name) == reader(args.output_dir / name), f"Reference mismatch: {name}")
    print(json.dumps({"status": "PASS", "checked_reference": args.check,
                      "sample_flow": summary["sample_flow"], "audio_verification": verification,
                      "restricted_files": sum(summary["variant_scope"]["retained_by_tts"].values())}, indent=2))


if __name__ == "__main__":
    main()
