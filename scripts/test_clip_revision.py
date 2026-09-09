"""Regression tests for published clip evidence and integrity failures."""

import hashlib
import json
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "results/clip_revision_20260909"
CHECKER = runpy.run_path(str(PACKAGE / "verify_tables.py"))


def rehash(root):
    records = [{"path": p.relative_to(root).as_posix(), "size": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
               for p in sorted(root.rglob("*"))
               if p.is_file() and p.name != "file_manifest.json"]
    (root / "file_manifest.json").write_text(json.dumps(records), encoding="utf-8")


class ClipRevisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "package"
        shutil.copytree(PACKAGE, self.root)

    def mutate(self, name, edit):
        path = self.root / name
        data = json.loads(path.read_text())
        edit(data)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        rehash(self.root)

    def check(self):
        CHECKER["verify"](self.root)

    def test_portable_full_verifier(self):
        result = subprocess.run([sys.executable, "-B", "-S", str(self.root / "verify.py")],
                                cwd=self.temp.name, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_optimized_python(self):
        result = subprocess.run([sys.executable, "-B", "-O", "-S",
                                 str(self.root / "verify.py")],
                                text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Do not use -O", result.stderr)

    def test_changed_audio_hash(self):
        with (self.root / "audio/B013_repaired_r1.wav").open("ab") as handle:
            handle.write(b"changed")
        with self.assertRaisesRegex(ValueError, "Manifest size mismatch"):
            self.check()

    def test_missing_audio(self):
        (self.root / "audio/B013_repaired_r1.wav").unlink()
        with self.assertRaisesRegex(ValueError, "package inventory"):
            self.check()

    def test_unlisted_file(self):
        (self.root / "unexpected.txt").write_text("unlisted")
        with self.assertRaisesRegex(ValueError, "package inventory"):
            self.check()

    def test_path_traversal(self):
        path = self.root / "file_manifest.json"
        data = json.loads(path.read_text())
        data[0]["path"] = "../outside"
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, "Unsafe manifest path"):
            self.check()

    def test_false_summary_after_rehash(self):
        self.mutate("qwen_surface_paired_test_effective_44.json",
                    lambda d: d.update(p_value=0.5))
        with self.assertRaisesRegex(ValueError, "Summary mismatch"):
            self.check()

    def test_mixed_mimo_label_after_rehash(self):
        self.mutate("mimo/selected_records_46.json",
                    lambda rows: next(r for r in rows if r["review_id"] == "B017")
                    .update(selected_label="exposed"))
        with self.assertRaisesRegex(ValueError, "MiMo label counts"):
            self.check()

    def test_identity_inclusion_after_rehash(self):
        self.mutate("paired_records_46.json",
                    lambda rows: rows[0].update(effective_context_reduction=True))
        with self.assertRaisesRegex(ValueError, "Integrity/paired mismatch"):
            self.check()

    def test_control_output_after_rehash(self):
        self.mutate("qwen_outputs_12.json",
                    lambda rows: next(r for r in rows if r["item_id"].endswith("_full_control"))
                    .update(asr_text="wrong control text"))
        with self.assertRaisesRegex(ValueError, "Control output mismatch"):
            self.check()


if __name__ == "__main__":
    unittest.main()
