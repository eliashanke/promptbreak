import unittest
from pathlib import Path

from build_results_dashboard import build_dashboard_data


class ResultsDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build_dashboard_data()

    def test_uses_only_canonical_comparison_runs(self):
        self.assertEqual(
            [run["id"] for run in self.data["runs"]],
            ["gemma-original", "gemma-tuned", "qwen4", "qwen27"],
        )
        self.assertTrue(all("raw-parser-errors" not in run["source"]["file"] for run in self.data["runs"]))

    def test_qwen_27b_report_is_repaired_and_error_free(self):
        run = next(run for run in self.data["runs"] if run["id"] == "qwen27")
        self.assertEqual(run["observations"], 150)
        self.assertEqual(run["repair"]["replaced_observations"], 14)
        self.assertEqual(sum(config["errors"] for config in run["configs"]), 0)

    def test_dashboard_exposes_security_utility_and_rainbow_metrics(self):
        run = next(run for run in self.data["runs"] if run["id"] == "qwen4")
        full = next(config for config in run["configs"] if config["id"] == "full_pipeline")
        self.assertEqual(full["asr"], 0.0)
        self.assertEqual(full["inputFpr"], 0.0)
        self.assertEqual(full["benignBlock"], 13.3)
        self.assertEqual(len(self.data["rainbows"]), 2)
        self.assertEqual(self.data["rainbows"][1]["coverage"], 100.0)

    def test_api_cost_inputs_and_pricing_sources_are_explicit(self):
        run = next(run for run in self.data["runs"] if run["id"] == "qwen27")
        self.assertTrue(all(config["tokens"] == config["promptTokens"] + config["completionTokens"] for config in run["configs"]))
        profile = next(profile for profile in self.data["pricingProfiles"] if profile["id"] == "qwen35-27b-frankfurt")
        self.assertEqual(profile["inputPerMillionUsd"], 0.086)
        self.assertEqual(profile["outputPerMillionUsd"], 0.688)
        self.assertEqual(profile["match"], "exact")
        self.assertTrue(profile["sourceUrl"].startswith("https://"))

    def test_dashboard_has_accessible_metric_explanations(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "dashboard" / "index.html").read_text(encoding="utf-8")
        script = (root / "dashboard" / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="info-modal"', html)
        self.assertIn('aria-labelledby="info-modal-title"', html)
        self.assertIn('data-info=', script)
        self.assertIn('modal.showModal()', script)

    def test_dashboard_uses_live_results_api_and_links_back_to_lab(self):
        root = Path(__file__).resolve().parents[1]
        html = (root / "dashboard" / "index.html").read_text(encoding="utf-8")
        script = (root / "dashboard" / "app.js").read_text(encoding="utf-8")
        lab = (root / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('fetch("/api/results"', script)
        self.assertNotIn('src="data.js"', html)
        self.assertNotIn("README.md", html)
        self.assertIn('<a class="brand" href="/">', html)
        self.assertIn('href="/">OPEN LAB', html)
        self.assertIn('href="/dashboard/">RESULTS', lab)


if __name__ == "__main__":
    unittest.main()
