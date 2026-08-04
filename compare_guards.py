"""Compare Promptbreak, Llama Guard, and ShieldGemma on a fixed local dataset."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from tqdm import tqdm

from main import (
    DEFAULT_GUARD_THRESHOLD,
    DEFAULT_MODEL,
    DEFENSE_PRESETS,
    LEVEL_BY_ID,
    LAYER_IDS,
    run_defense,
)


ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET = ROOT / "data" / "guard-evaluation.json"

CONFIGURATIONS: Dict[str, Dict[str, Any]] = {
    "prompt_only": {
        "backend": None,
        "layers": DEFENSE_PRESETS["prompt_only"],
        "description": "Target model protected only by its system prompt.",
    },
    "promptbreak_guard": {
        "backend": "promptbreak",
        "layers": DEFENSE_PRESETS["input_guard"],
        "description": "Promptbreak heuristics plus a task-specific LLM classifier.",
    },
    "llama_guard": {
        "backend": "llama_guard",
        "layers": {**{layer: False for layer in LAYER_IDS}, "llm_guard": True},
        "description": "Out-of-the-box Llama Guard input moderation.",
    },
    "shieldgemma": {
        "backend": "shieldgemma",
        "layers": {**{layer: False for layer in LAYER_IDS}, "llm_guard": True},
        "description": "Out-of-the-box ShieldGemma input moderation.",
    },
    "full_pipeline": {
        "backend": "promptbreak",
        "layers": DEFENSE_PRESETS["full_pipeline"],
        "description": "Promptbreak classifier plus hardening, context, and output filters.",
    },
}


def load_dataset(path: Path = DEFAULT_DATASET) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("Dataset enthält keine Fälle")
    ids = set()
    for case in cases:
        missing = {"id", "kind", "category", "level", "prompt", "history"} - set(case)
        if missing:
            raise ValueError(f"Fall ohne Pflichtfelder {sorted(missing)}: {case}")
        if case["id"] in ids:
            raise ValueError(f"Doppelte Fall-ID: {case['id']}")
        ids.add(case["id"])
        if case["kind"] not in {"attack", "benign"}:
            raise ValueError(f"Ungültiger kind-Wert in {case['id']}")
        if int(case["level"]) not in LEVEL_BY_ID:
            raise ValueError(f"Unbekanntes Level in {case['id']}")
        if not isinstance(case["history"], list):
            raise ValueError(f"history muss eine Liste sein: {case['id']}")
    return payload


def percentile(values: Iterable[float], percentile_value: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    rank = max(0, math.ceil(percentile_value / 100 * len(ordered)) - 1)
    return round(ordered[rank], 1)


def safe_ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def safe_mean(values: Iterable[float]) -> float:
    collected = list(values)
    return round(statistics.fmean(collected), 1) if collected else 0.0


def summarize_rows(
    rows: List[Dict[str, Any]],
    *,
    input_price_per_million: Optional[float] = None,
    output_price_per_million: Optional[float] = None,
) -> Dict[str, Any]:
    attacks = [row for row in rows if row["kind"] == "attack"]
    benign = [row for row in rows if row["kind"] == "benign"]
    tp = sum(bool(row["blocked"]) for row in attacks)
    fn = len(attacks) - tp
    fp = sum(bool(row["blocked"]) for row in benign)
    tn = len(benign) - fp
    precision = safe_ratio(tp, tp + fp)
    recall = safe_ratio(tp, tp + fn)
    f1 = safe_ratio(2 * precision * recall, precision + recall)
    warm_rows = [row for row in rows if row["repetition"] > 1] or rows
    total_prompt_tokens = sum(int(row["usage"]["prompt_tokens"]) for row in rows)
    total_completion_tokens = sum(int(row["usage"]["completion_tokens"]) for row in rows)
    hypothetical_cost = None
    if input_price_per_million is not None and output_price_per_million is not None:
        hypothetical_cost = round(
            total_prompt_tokens / 1_000_000 * input_price_per_million
            + total_completion_tokens / 1_000_000 * output_price_per_million,
            6,
        )
    return {
        "cases": len(rows),
        "attack_success_rate": round(
            safe_ratio(sum(bool(row["breach"]) for row in attacks), len(attacks)) * 100,
            1,
        ),
        "attack_block_rate": round(recall * 100, 1),
        "false_positive_rate": round(safe_ratio(fp, len(benign)) * 100, 1),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "confusion_matrix": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        "latency_ms": {
            "mean_all": safe_mean(row["latency_ms"] for row in rows),
            "mean_attack": safe_mean(row["latency_ms"] for row in attacks),
            "mean_benign": safe_mean(row["latency_ms"] for row in benign),
            "p50_warm": percentile((row["latency_ms"] for row in warm_rows), 50),
            "p95_warm": percentile((row["latency_ms"] for row in warm_rows), 95),
            "load_total": round(
                sum(float(row["usage"]["load_duration_ms"]) for row in rows),
                1,
            ),
        },
        "compute": {
            "model_calls_total": sum(int(row["usage"]["model_calls"]) for row in rows),
            "model_calls_per_case": round(
                statistics.fmean(row["usage"]["model_calls"] for row in rows),
                3,
            ),
            "prompt_tokens_total": total_prompt_tokens,
            "completion_tokens_total": total_completion_tokens,
            "tokens_per_case": round(
                safe_ratio(total_prompt_tokens + total_completion_tokens, len(rows)),
                1,
            ),
            "local_api_cost": 0,
            "hypothetical_api_cost": hypothetical_cost,
        },
        "errors": sum(bool(row.get("guard_error")) for row in rows),
    }


def run_comparison(
    dataset: Dict[str, Any],
    *,
    target_model: str,
    promptbreak_model: str,
    llama_guard_model: str,
    shieldgemma_model: str,
    configurations: List[str],
    repeats: int,
    max_cases: Optional[int] = None,
    case_ids: Optional[List[str]] = None,
    promptbreak_threshold: float = DEFAULT_GUARD_THRESHOLD,
    input_price_per_million: Optional[float] = None,
    output_price_per_million: Optional[float] = None,
) -> Dict[str, Any]:
    model_by_backend = {
        "promptbreak": promptbreak_model,
        "llama_guard": llama_guard_model,
        "shieldgemma": shieldgemma_model,
    }
    cases = list(dataset["cases"])
    if case_ids:
        requested = set(case_ids)
        cases = [case for case in cases if case["id"] in requested]
        missing = requested - {case["id"] for case in cases}
        if missing:
            raise ValueError(f"Unbekannte Fall-IDs: {sorted(missing)}")
    if max_cases is not None:
        cases = cases[:max_cases]
    rows: List[Dict[str, Any]] = []
    started = time.perf_counter()
    total = len(configurations) * repeats * len(cases)
    with tqdm(
        total=total,
        desc="Guard comparison",
        unit="case",
        dynamic_ncols=True,
        smoothing=0.1,
    ) as progress:
        for config_index, configuration in enumerate(configurations, start=1):
            spec = CONFIGURATIONS[configuration]
            backend = spec["backend"]
            for repetition in range(1, repeats + 1):
                progress.set_description(
                    f"[{config_index}/{len(configurations)}] {configuration} "
                    f"· repetition {repetition}/{repeats}"
                )
                for case in cases:
                    result = run_defense(
                        LEVEL_BY_ID[int(case["level"])],
                        "custom",
                        target_model,
                        str(case["prompt"]),
                        list(case["history"]),
                        dict(spec["layers"]),
                        guard_backend=backend or "promptbreak",
                        guard_model=model_by_backend.get(backend),
                        guard_threshold=promptbreak_threshold,
                    )
                    guard = result.get("guard") or {}
                    rows.append(
                        {
                            "configuration": configuration,
                            "repetition": repetition,
                            "case_id": case["id"],
                            "kind": case["kind"],
                            "category": case["category"],
                            "level": case["level"],
                            "blocked": result["blocked"],
                            "breach": result["breach"],
                            "latency_ms": result["latency_ms"],
                            "usage": result["usage"],
                            "guard_backend": backend,
                            "guard_model": model_by_backend.get(backend),
                            "guard_label": guard.get("raw_label") or guard.get("category"),
                            "guard_error": guard.get("error"),
                            "guard_decisions": result.get("guard_decisions"),
                            "trace": result["trace"],
                        }
                    )
                    progress.set_postfix_str(str(case["id"]), refresh=False)
                    progress.update(1)
    summaries = {
        configuration: summarize_rows(
            [row for row in rows if row["configuration"] == configuration],
            input_price_per_million=input_price_per_million,
            output_price_per_million=output_price_per_million,
        )
        for configuration in configurations
    }
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {
            "name": dataset.get("name"),
            "version": dataset.get("version"),
            "case_count": len(cases),
        },
        "target_model": target_model,
        "guard_models": model_by_backend,
        "promptbreak_threshold": promptbreak_threshold,
        "repeats": repeats,
        "configurations": configurations,
        "summaries": summaries,
        "rows": rows,
        "runtime_ms": round((time.perf_counter() - started) * 1000),
        "cost_note": (
            "Local Ollama API cost is zero. Model calls, tokens, wall-clock latency, "
            "and model load time are reported as computational-cost proxies."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare local Promptbreak guard models")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--target-model", default=DEFAULT_MODEL)
    parser.add_argument("--promptbreak-model", default=DEFAULT_MODEL)
    parser.add_argument("--llama-guard-model", default="llama-guard3:1b")
    parser.add_argument("--shieldgemma-model", default="shieldgemma:2b")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--promptbreak-threshold",
        type=float,
        default=DEFAULT_GUARD_THRESHOLD,
        help="Confidence threshold for the task-specific Gemma guard.",
    )
    parser.add_argument("--max-cases", type=int)
    parser.add_argument(
        "--case-id",
        action="append",
        dest="case_ids",
        help="Run only the selected case ID; may be specified multiple times.",
    )
    parser.add_argument(
        "--config",
        action="append",
        choices=tuple(CONFIGURATIONS),
        dest="configurations",
    )
    parser.add_argument("--input-price-per-million", type=float)
    parser.add_argument("--output-price-per-million", type=float)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate the dataset and print the planned matrix without calling Ollama.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.repeats < 1:
        raise SystemExit("--repeats muss mindestens 1 sein")
    if not 0 <= args.promptbreak_threshold <= 1:
        raise SystemExit("--promptbreak-threshold muss zwischen 0 und 1 liegen")
    if (args.input_price_per_million is None) != (args.output_price_per_million is None):
        raise SystemExit("Für eine API-Schätzung müssen beide Tokenpreise gesetzt sein")
    dataset = load_dataset(args.dataset)
    configurations = args.configurations or list(CONFIGURATIONS)
    if args.dry_run:
        cases = list(dataset["cases"])
        if args.case_ids:
            requested = set(args.case_ids)
            cases = [case for case in cases if case["id"] in requested]
            missing = requested - {case["id"] for case in cases}
            if missing:
                raise SystemExit(f"Unbekannte Fall-IDs: {sorted(missing)}")
        if args.max_cases is not None:
            cases = cases[:args.max_cases]
        attacks = sum(case["kind"] == "attack" for case in cases)
        benign = sum(case["kind"] == "benign" for case in cases)
        print(
            json.dumps(
                {
                    "dataset": dataset["name"],
                    "cases": len(cases),
                    "attacks": attacks,
                    "benign": benign,
                    "configurations": configurations,
                    "repeats": args.repeats,
                    "promptbreak_threshold": args.promptbreak_threshold,
                    "planned_runs": len(cases) * len(configurations) * args.repeats,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return
    report = run_comparison(
        dataset,
        target_model=args.target_model,
        promptbreak_model=args.promptbreak_model,
        llama_guard_model=args.llama_guard_model,
        shieldgemma_model=args.shieldgemma_model,
        configurations=configurations,
        repeats=args.repeats,
        max_cases=args.max_cases,
        case_ids=args.case_ids,
        promptbreak_threshold=args.promptbreak_threshold,
        input_price_per_million=args.input_price_per_million,
        output_price_per_million=args.output_price_per_million,
    )
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
