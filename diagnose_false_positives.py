"""Attribute benign Promptbreak false positives to heuristics or the LLM classifier."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tqdm import tqdm

from compare_guards import DEFAULT_DATASET, load_dataset
from main import DEFAULT_GUARD_THRESHOLD, classify_prompt, heuristic_risk


ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "evaluation-results" / "false-positive-attribution-2026-07-30.json"


def diagnose(
    model: str,
    dataset_path: Path,
    confidence_threshold: float = DEFAULT_GUARD_THRESHOLD,
) -> dict[str, Any]:
    dataset = load_dataset(dataset_path)
    rows = []
    benign_cases = [case for case in dataset["cases"] if case["kind"] == "benign"]
    for case in tqdm(
        benign_cases,
        desc="False-positive attribution",
        unit="case",
        dynamic_ncols=True,
        smoothing=0.1,
    ):
        heuristic_blocked, heuristic_reasons = heuristic_risk(str(case["prompt"]))
        llm = classify_prompt(
            model,
            str(case["prompt"]),
            use_heuristics=False,
            confidence_threshold=confidence_threshold,
        )
        llm_blocked = bool(llm.get("blocked"))
        if heuristic_blocked and llm_blocked:
            attribution = "both"
        elif heuristic_blocked:
            attribution = "heuristics_only"
        elif llm_blocked:
            attribution = "llm_only"
        else:
            attribution = "neither"
        rows.append(
            {
                "case_id": case["id"],
                "category": case["category"],
                "prompt": case["prompt"],
                "heuristics": {
                    "blocked": heuristic_blocked,
                    "reasons": heuristic_reasons,
                },
                "llm_only": {
                    "blocked": llm_blocked,
                    "malicious": bool(llm.get("malicious")),
                    "confidence": llm.get("confidence"),
                    "category": llm.get("category"),
                    "reason": llm.get("reason"),
                    "error": llm.get("error"),
                    "usage": llm.get("usage"),
                },
                "combined_blocked": heuristic_blocked or llm_blocked,
                "attribution": attribution,
            }
        )
    counts = {
        key: sum(row["attribution"] == key for row in rows)
        for key in ("heuristics_only", "llm_only", "both", "neither")
    }
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset": dataset.get("name"),
        "model": model,
        "confidence_threshold": confidence_threshold,
        "benign_cases": len(rows),
        "summary": {
            "heuristics_blocked": sum(row["heuristics"]["blocked"] for row in rows),
            "llm_only_blocked": sum(row["llm_only"]["blocked"] for row in rows),
            "combined_blocked": sum(row["combined_blocked"] for row in rows),
            "attribution": counts,
            "errors": sum(bool(row["llm_only"]["error"]) for row in rows),
        },
        "rows": rows,
        "scope_note": (
            "This report attributes input-guard false positives only. Context and "
            "output layers are intentionally not re-run; end-to-end benign blocks "
            "caused by caught model leaks must be interpreted separately."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gemma4:latest")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--threshold",
        type=float,
        default=DEFAULT_GUARD_THRESHOLD,
        help="Confidence threshold used for the Gemma-only decision.",
    )
    args = parser.parse_args()
    if not 0 <= args.threshold <= 1:
        raise SystemExit("--threshold muss zwischen 0 und 1 liegen")
    report = diagnose(args.model, args.dataset, args.threshold)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
