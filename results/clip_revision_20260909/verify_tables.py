"""Additional manifest, input-linkage, and summary checks for public release."""

import csv
import hashlib
import json
import math
from collections import Counter
from pathlib import Path, PurePosixPath


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(root, name):
    return json.loads((root / name).read_text(encoding="utf-8"))


def manifest_check(root):
    manifest = load(root, "file_manifest.json")
    names = [r["path"] for r in manifest]
    require(len(names) == len(set(names)), "Duplicate manifest path")
    for name in names:
        relative = PurePosixPath(name)
        require(not relative.is_absolute() and ".." not in relative.parts
                and relative.as_posix() == name, "Unsafe manifest path")
    files = []
    for path in root.rglob("*"):
        require(not path.is_symlink(), "Package contains a symlink")
        if path.is_file() and path.name != "file_manifest.json":
            files.append(path.relative_to(root).as_posix())
    require(set(names) == set(files), "Manifest does not cover exact package inventory")
    for item in manifest:
        data = (root / item["path"]).read_bytes()
        require(len(data) == item["size"], "Manifest size mismatch: " + item["path"])
        require(hashlib.sha256(data).hexdigest() == item["sha256"],
                "Manifest hash mismatch: " + item["path"])


def summarize(rows, clip_key="selected_clip_label"):
    require(bool(rows), "Empty paired population")
    matrix = [[sum(r["full_label"] == a and r[clip_key] == b for r in rows)
               for b in "SWO"] for a in "SWO"]
    require(sum(map(sum, matrix)) == len(rows), "Unknown paired label")
    forward = sum(matrix[0][1:])
    reverse = matrix[1][0] + matrix[2][0]
    n_discordant = forward + reverse
    p = min(1.0, 2 * sum(math.comb(n_discordant, k)
                         for k in range(min(forward, reverse) + 1))
            / 2 ** n_discordant)
    binary = [[matrix[0][0], forward],
              [reverse, sum(sum(row[1:]) for row in matrix[1:])]]
    return {
        "n": len(rows),
        "unique_scripts": len({r["case_id"] for r in rows}),
        "full_surface": sum(matrix[0]),
        "clip_surface": sum(row[0] for row in matrix),
        "matrix_rows_full_columns_clip_S_W_O": matrix,
        "matrix_rows_full_columns_clip_S_nonS": binary,
        "full_S_to_clip_W": matrix[0][1],
        "discordant_full_S_to_clip_nonS": forward,
        "discordant_full_nonS_to_clip_S": reverse,
        "p_value": p,
        "surface_proportion_change_clip_minus_full":
            (sum(row[0] for row in matrix) - sum(matrix[0])) / len(rows),
    }


def compare_summary(expected, actual, name):
    for key, value in actual.items():
        require(expected[key] == value, f"Summary mismatch: {name}/{key}")


def verify(root):
    root = Path(root)
    manifest_check(root)
    rows = load(root, "paired_records_46.json")
    indexed = {r["review_id"]: r for r in rows}
    require(len(rows) == len(indexed) == 46, "Expected 46 unique paired records")
    integrity = load(root, "integrity_records_46.json")
    require(len(integrity) == 46 and {r["review_id"] for r in integrity} == set(indexed),
            "Integrity IDs do not match paired IDs")
    for item in integrity:
        row = indexed[item["review_id"]]
        for key in ("probe_candidate_id", "case_id", "target", "raw_sha256",
                    "original_clip_sha256", "selected_clip_sha256",
                    "selected_audio_version", "selected_duration_seconds",
                    "effective_context_reduction"):
            require(item[key] == row[key], "Integrity/paired mismatch: " + key)
        require(item["selected_interval_seconds"] ==
                [row["interval_start_seconds"], row["interval_end_seconds"]],
                "Integrity interval mismatch")
        require(row["effective_context_reduction"] ==
                (row["raw_sha256"] != row["selected_clip_sha256"]),
                "Identity incorrectly counted as crop")
        require(row["selected_binary_endpoint"] ==
                ("S" if row["selected_clip_label"] == "S" else "non-S"),
                "Binary endpoint mismatch")

    effective = [r for r in rows if r["effective_context_reduction"]]
    historical = [r for r in rows if r["selected_audio_version"] == "original"]
    identities = [r for r in rows if not r["effective_context_reduction"]]
    statistics = load(root, "paired_statistics.json")
    populations = {
        "historical_original_46": (rows, "original_clip_label"),
        "unchanged_integrity_passed_42_sensitivity": (historical, "selected_clip_label"),
        "repaired_selected_46_descriptive": (rows, "selected_clip_label"),
        "effective_context_reduction_44_primary": (effective, "selected_clip_label"),
        "identity_2_descriptive": (identities, "selected_clip_label"),
    }
    for name, (population, key) in populations.items():
        compare_summary(statistics["summaries"][name], summarize(population, key), name)
    primary = summarize(effective)
    compare_summary(load(root, "qwen_surface_paired_test_effective_44.json"),
                    primary, "primary-test")
    for label in "WO":
        alternative = [dict(r, selected_clip_label=label) if r["review_id"] == "B017"
                       else r for r in effective]
        compare_summary(statistics["B017_W_or_O_sensitivity_on_effective_44"][label],
                        summarize(alternative), "B017-" + label)
    with (root / "qwen_paired_transition_matrix_effective_44.csv").open(
            encoding="utf-8-sig", newline="") as handle:
        cells = list(csv.DictReader(handle))
    require(len(cells) == 9, "Expected all nine paired cells")
    expected = {(a, b): primary["matrix_rows_full_columns_clip_S_W_O"][i][j]
                for i, a in enumerate("SWO") for j, b in enumerate("SWO")}
    require({(r["full_outcome"], r["clip_outcome"]): int(r["count"]) for r in cells}
            == expected and all(int(r["n"]) == 44 for r in cells),
            "CSV paired matrix mismatch")
    with (root / "paired_records_46.csv").open(encoding="utf-8-sig", newline="") as handle:
        csv_records = list(csv.DictReader(handle))
    require(len(csv_records) == 46 and
            {r["review_id"] for r in csv_records} == set(indexed),
            "CSV paired records mismatch")
    for item in csv_records:
        for key, value in item.items():
            require(value == str(indexed[item["review_id"]][key]),
                    "CSV/JSON paired record mismatch: " + key)
    controls = load(root, "reproducibility_controls_8.json")
    outputs = {r["item_id"]: r for r in load(root, "qwen_outputs_12.json")}
    require(len({c["item_id"] for c in controls}) == 8, "Duplicate control")
    for c in controls:
        output, pair = outputs[c["item_id"]], indexed[c["review_id"]]
        require(c["input_sha256"] == output["input_sha256"], "Control input mismatch")
        require(c["rerun_transcript"] == output["asr_text"] == c["baseline_transcript"],
                "Control output mismatch")
        field = "original_clip_transcript" if c["condition"] == "original_clip_control" else "full_transcript"
        require(c["baseline_transcript"] == pair[field], "Control baseline mismatch")
    mimo = load(root, "mimo/selected_records_46.json")
    require(len(mimo) == 46 and {r["review_id"] for r in mimo} == set(indexed),
            "MiMo IDs differ from Qwen")
    for item in mimo:
        pair = indexed[item["review_id"]]
        require(item["effective_context_reduction"] == pair["effective_context_reduction"],
                "MiMo crop population differs from Qwen")
        require(item["audio_sha256"] == pair["selected_clip_sha256"], "MiMo audio mismatch")
    labels = Counter(r["selected_label"] for r in mimo if r["effective_context_reduction"])
    require(labels == {"exposed": 16, "still_masked": 13, "no_output": 12,
                       "other_transcript": 3}, "MiMo label counts differ")
    print("PASS complete manifest, paired summaries/CSV, integrity linkage and controls")
