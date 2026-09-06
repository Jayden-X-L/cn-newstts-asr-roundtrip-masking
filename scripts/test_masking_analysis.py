"""Focused regression tests for the portable analysis entrypoint."""

import json
import tempfile
import unittest
from pathlib import Path

import derive_masking_analysis as analysis

ROOT = Path(__file__).resolve().parents[1]


class AnalysisTests(unittest.TestCase):
    def test_score_relation_scope(self):
        self.assertTrue(analysis.score_relation_check("13-11", "十三比十一", "十三至十一")[0])
        self.assertFalse(analysis.score_relation_check("13-11", "十三比十一", "十三比十一")[0])
        self.assertFalse(analysis.score_relation_check("13-11", "十三比十一", "十二至十一")[0])
        self.assertFalse(analysis.score_relation_check("88VIP", "八十八VIP", "八十八伏IP")[0])

    def test_missing_inputs_fail_without_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ValueError, "Missing public input"):
                analysis.derive(root, root / "output")
            self.assertFalse((root / "output").exists())

    def test_missing_audio_fails_without_output(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "output"
            with self.assertRaisesRegex(ValueError, "Missing WAV"):
                analysis.derive(ROOT, out, audio_root=Path(temp))
            self.assertFalse(out.exists())

    def test_wrong_zip_fails_without_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            wrong = root / "wrong.zip"
            wrong.write_bytes(b"not the published archive")
            with self.assertRaisesRegex(ValueError, "ZIP size mismatch"):
                analysis.derive(ROOT, root / "output", archive=wrong)
            self.assertFalse((root / "output").exists())

    def test_default_is_explicitly_inventory_only(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            _, verification = analysis.derive(ROOT, out)
            self.assertEqual(verification["mode"], "inventory_only")
            self.assertEqual(verification["verified_audio_files"], 0)
            for name in analysis.RESULT_FILES:
                read = analysis.read_csv if name.endswith(".csv") else lambda p: json.loads(p.read_text())
                self.assertEqual(read(ROOT / "results/masking_revision" / name), read(out / name), name)


if __name__ == "__main__":
    unittest.main()
