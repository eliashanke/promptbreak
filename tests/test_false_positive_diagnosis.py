import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.diagnose_false_positives import diagnose_from_sweep


class SweepAttributionTests(unittest.TestCase):
    @patch("experiments.diagnose_false_positives.load_dataset")
    def test_zero_error_sweep_is_reused_without_model_calls(self, load_dataset):
        load_dataset.return_value = {
            "name": "holdout",
            "version": "1",
            "cases": [
                {
                    "id": "benign-1",
                    "kind": "benign",
                    "category": "roleplay",
                    "prompt": "Explain roleplay.",
                }
            ],
        }
        sweep = {
            "dataset": {"name": "holdout", "version": "1"},
            "model": "guard",
            "errors": 0,
            "rows": [
                {
                    "case_id": "benign-1",
                    "heuristic": {"blocked": False, "reasons": []},
                    "llm": {
                        "malicious": False,
                        "confidence": 0.99,
                        "category": "safe",
                        "reason": "Benign.",
                        "error": None,
                        "usage": {"model_calls": 1},
                    },
                }
            ],
        }
        report = diagnose_from_sweep(sweep, Path("unused.json"), 0.55)
        self.assertEqual(report["summary"]["combined_blocked"], 0)
        self.assertEqual(report["summary"]["attribution"]["neither"], 1)
        self.assertIn("no additional model calls", report["derived_from"])

    @patch("experiments.diagnose_false_positives.load_dataset")
    def test_sweep_with_errors_is_rejected(self, load_dataset):
        with self.assertRaises(ValueError):
            diagnose_from_sweep({"errors": 1}, Path("unused.json"))
        load_dataset.assert_not_called()


if __name__ == "__main__":
    unittest.main()
