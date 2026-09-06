"""Focused regression tests for the portable analysis entrypoint."""

import json
import tempfile
import unittest
from pathlib import Path

import derive_masking_analysis as analysis

ROOT = Path(__file__).resolve().parents[1]


class AnalysisTests(unittest.TestCase):
    def test_exact_mcnemar(self):
        self.assertEqual(analysis.exact_mcnemar_p(12, 0), 0.00048828125)
        self.assertEqual(analysis.exact_mcnemar_p(0, 12), 0.00048828125)
        self.assertEqual(analysis.exact_mcnemar_p(0, 0), 1.0)
        self.assertEqual(analysis.exact_mcnemar_p(4, 4), 1.0)
        with self.assertRaises(ValueError):
            analysis.exact_mcnemar_p(-1, 0)

    def test_score_scope_and_paired_endpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)
            analysis.derive(ROOT, out)
            scope = json.loads((out / "strict_score_scope_summary.json").read_text())
            self.assertEqual((scope["recordings"], scope["unique_scripts"], scope["scripts_with_both_tts"]), (41, 24, 17))
            markers = analysis.read_csv(out / "strict_score_marker_counts.csv")
            self.assertEqual({(r["tts"], r["heard_relation_marker"]): int(r["recordings"]) for r in markers if int(r["recordings"])},
                             {("MiMo", "至"): 18, ("CosyVoice", "减"): 23})
            paired = json.loads((out / "qwen_surface_paired_test.json").read_text())
            self.assertEqual(paired["matrix_rows_full_columns_clip_S_nonS"], [[7, 12], [0, 27]])
            self.assertEqual(paired["p_value"], 0.00048828125)

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
