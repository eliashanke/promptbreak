"""Compare target-model susceptibility with a fixed defense configuration.

This runner deliberately holds the dataset, guard model, thresholds, and
hardware constant. Only the target model changes between runs.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from tqdm import tqdm

from experiments.compare_guards import CONFIGURATIONS, DEFAULT_DATASET, load_dataset, run_comparison
from promptbreak.main import DEFAULT_GUARD_THRESHOLD
from promptbreak.model_adapters import (
    DEFAULT_TARGET_MODEL_ALIASES,
    MODEL_PROFILES,
    describe_model,
    resolve_model_tag,
)


def run_model_comparison(
    dataset: Dict[str, Any],
    *,
    target_models: List[str],
    configurations: List[str],
    guard_model: str,
    llama_guard_model: str,
    shieldgemma_model: str,
    repeats: int,
    max_cases: Optional[int] = None,
    case_ids: Optional[List[str]] = None,
    promptbreak_threshold: float = DEFAULT_GUARD_THRESHOLD,
) -> Dict[str, Any]:
    reports = []
    started = time.perf_counter()
    evaluated_case_count = 0
    for model in tqdm(target_models, desc="Target models", unit="model", dynamic_ncols=True):
        report = run_comparison(
            dataset,
            target_model=model,
            promptbreak_model=guard_model,
            llama_guard_model=llama_guard_model,
            shieldgemma_model=shieldgemma_model,
            configurations=configurations,
            repeats=repeats,
            max_cases=max_cases,
            case_ids=case_ids,
            promptbreak_threshold=promptbreak_threshold,
        )
        evaluated_case_count = int(report["dataset"]["case_count"])
        reports.append(
            {
                "model": describe_model(model),
                "resolved_target_model": resolve_model_tag(model),
                "summaries": report["summaries"],
                "rows": report["rows"],
                "runtime_ms": report["runtime_ms"],
            }
        )
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "experiment": "target-model prompt-injection comparison",
        "dataset": {
            "name": dataset.get("name"),
            "version": dataset.get("version"),
            "case_count": evaluated_case_count,
        },
        "controlled_guard_model": resolve_model_tag(guard_model),
        "promptbreak_threshold": promptbreak_threshold,
        "configurations": configurations,
        "repeats": repeats,
        "model_runs": reports,
        "runtime_ms": round((time.perf_counter() - started) * 1000),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare Ollama target models")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        help=(
            "Registry alias or raw Ollama tag; repeat for multiple models. "
            f"Known aliases: {', '.join(MODEL_PROFILES)}"
        ),
    )
    parser.add_argument("--guard-model", default="gemma4")
    parser.add_argument("--llama-guard-model", default="llama-guard3:1b")
    parser.add_argument("--shieldgemma-model", default="shieldgemma:2b")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--max-cases", type=int)
    parser.add_argument("--case-id", action="append", dest="case_ids")
    parser.add_argument(
        "--config",
        action="append",
        choices=tuple(CONFIGURATIONS),
        dest="configurations",
    )
    parser.add_argument("--promptbreak-threshold", type=float, default=DEFAULT_GUARD_THRESHOLD)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.repeats < 1:
        raise SystemExit("--repeats muss mindestens 1 sein")
    if not 0 <= args.promptbreak_threshold <= 1:
        raise SystemExit("--promptbreak-threshold muss zwischen 0 und 1 liegen")
    dataset = load_dataset(args.dataset)
    models = args.models or list(DEFAULT_TARGET_MODEL_ALIASES)
    configurations = args.configurations or ["prompt_only", "full_pipeline"]
    selected_cases = list(dataset["cases"])
    if args.case_ids:
        requested = set(args.case_ids)
        selected_cases = [case for case in selected_cases if case["id"] in requested]
        missing = requested - {case["id"] for case in selected_cases}
        if missing:
            raise SystemExit(f"Unbekannte Fall-IDs: {sorted(missing)}")
    if args.max_cases is not None:
        selected_cases = selected_cases[: args.max_cases]

    if args.dry_run:
        payload = {
            "models": [describe_model(model) for model in models],
            "configurations": configurations,
            "cases": len(selected_cases),
            "repeats": args.repeats,
            "planned_runs": len(models) * len(configurations) * len(selected_cases) * args.repeats,
            "downloads_are_not_started": True,
        }
    else:
        payload = run_model_comparison(
            dataset,
            target_models=models,
            configurations=configurations,
            guard_model=args.guard_model,
            llama_guard_model=args.llama_guard_model,
            shieldgemma_model=args.shieldgemma_model,
            repeats=args.repeats,
            max_cases=args.max_cases,
            case_ids=args.case_ids,
            promptbreak_threshold=args.promptbreak_threshold,
        )
    rendered = json.dumps(payload, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
