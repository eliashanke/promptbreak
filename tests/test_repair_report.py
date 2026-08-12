import unittest

from experiments.repair_guard_report import repair_report


def row(case_id, error=None, blocked=False):
    return {
        "configuration": "promptbreak_guard",
        "repetition": 1,
        "case_id": case_id,
        "kind": "attack",
        "blocked": blocked,
        "breach": not blocked,
        "model_leak_caught": False,
        "latency_ms": 1,
        "usage": {
            "model_calls": 1,
            "prompt_tokens": 1,
            "completion_tokens": 1,
            "load_duration_ms": 0,
        },
        "timing": {},
        "guard_error": error,
        "trace": {"input_guard": "BLOCKED" if blocked else "PASSED"},
    }


def report(rows):
    return {
        "dataset": {"name": "test", "version": "1"},
        "target_model": "target",
        "guard_models": {"promptbreak": "guard"},
        "promptbreak_threshold": 0.55,
        "repeats": 1,
        "configurations": ["promptbreak_guard"],
        "rows": rows,
        "runtime_ms": 10,
    }


class RepairReportTests(unittest.TestCase):
    def test_only_failed_observations_are_replaced(self):
        good = row("good", blocked=False)
        failed = row("failed", error="invalid JSON", blocked=False)
        replacement = row("failed", blocked=True)
        extra = row("good", blocked=True)
        repaired = repair_report(
            report([good, failed]),
            report([replacement, extra]),
            base_name="base.json",
            patch_name="patch.json",
        )
        self.assertIs(repaired["rows"][0], good)
        self.assertTrue(repaired["rows"][1]["blocked"])
        self.assertEqual(repaired["repair"]["replaced_observations"], 1)

    def test_rejects_missing_or_failed_replacements(self):
        base = report([row("failed", error="invalid JSON")])
        with self.assertRaises(ValueError):
            repair_report(base, report([]), base_name="base.json", patch_name="patch.json")
        with self.assertRaises(ValueError):
            repair_report(
                base,
                report([row("failed", error="still invalid")]),
                base_name="base.json",
                patch_name="patch.json",
            )


if __name__ == "__main__":
    unittest.main()
