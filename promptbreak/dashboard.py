"""Build compact dashboard data from the versioned evaluation reports."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "evaluation-results"
FINETUNING = ROOT / "finetuning"
DEFAULT_OUTPUT = ROOT / "dashboard" / "data.js"

RUN_SPECS = (
    ("gemma-original", "Gemma 4 · original", "full-guard-comparison-2026-07-30.json"),
    ("gemma-tuned", "Gemma 4 · revised guard (1× validation)", "tuned-guard-validation-2026-07-30.json"),
    ("qwen4", "Qwen 3.5 · 4B", "qwen35-4b-full-guard-comparison-2026-08-07.json"),
    ("qwen27", "Qwen 3.5 · 27B", "qwen35-27b-full-guard-comparison-2026-08-07.json"),
)

THRESHOLD_SPECS = (
    ("gemma-original", "Gemma 4", "guard-threshold-sweep-2026-07-30.json"),
    ("qwen4", "Qwen 3.5 · 4B", "qwen35-4b-guard-threshold-sweep-2026-08-07.json"),
    ("qwen27", "Qwen 3.5 · 27B", "qwen35-27b-guard-threshold-sweep-2026-08-07.json"),
)

ATTRIBUTION_SPECS = (
    ("gemma-original", "false-positive-attribution-2026-07-30.json"),
    ("qwen4", "qwen35-4b-false-positive-attribution-2026-08-07.json"),
    ("qwen27", "qwen35-27b-false-positive-attribution-2026-08-07.json"),
)

RAINBOW_SPECS = (
    ("gemma8", "Gemma 4 · 8 mutations", "rainbow-lite-full-pipeline-2026-07-30.json"),
    ("qwen4-24", "Qwen 3.5 4B · 24 mutations", "rainbow-lite-qwen35-4b-24-2026-08-07.json"),
)

CONFIG_LABELS = {
    "prompt_only": "Prompt only",
    "promptbreak_guard": "Promptbreak guard",
    "llama_guard": "Llama Guard 3",
    "shieldgemma": "ShieldGemma",
    "full_pipeline": "Full pipeline",
}

PRICING_PROFILES = (
    {
        "id": "qwen35-27b-frankfurt",
        "label": "Qwen 3.5 27B · Frankfurt",
        "provider": "Alibaba Cloud Model Studio",
        "model": "qwen3.5-27b",
        "region": "Germany (Frankfurt), Global, ≤128K",
        "inputPerMillionUsd": 0.086,
        "outputPerMillionUsd": 0.688,
        "match": "exact",
        "note": "Exact model; non-thinking output price. Every recorded call is priced with this profile.",
        "sourceUrl": "https://www.alibabacloud.com/help/en/model-studio/model-pricing",
        "checkedAt": "2026-08-07",
    },
    {
        "id": "qwen35-flash-eu-proxy",
        "label": "Qwen 3.5 Flash · EU proxy",
        "provider": "Alibaba Cloud Model Studio",
        "model": "qwen3.5-flash",
        "region": "Germany (Frankfurt), EU, ≤1M",
        "inputPerMillionUsd": 0.1,
        "outputPerMillionUsd": 0.4,
        "match": "proxy",
        "note": "Pricing proxy only: Alibaba lists no direct Qwen 3.5 4B endpoint.",
        "sourceUrl": "https://www.alibabacloud.com/help/en/model-studio/model-pricing",
        "checkedAt": "2026-08-07",
    },
    {
        "id": "gemma4-ai-studio-free",
        "label": "Gemma 4 · AI Studio free tier",
        "provider": "Google AI for Developers",
        "model": "Gemma 4",
        "region": "Google AI Studio free tier",
        "inputPerMillionUsd": 0.0,
        "outputPerMillionUsd": 0.0,
        "match": "free-tier",
        "note": "Google lists Gemma 4 as free of charge; a paid token tier is not available.",
        "sourceUrl": "https://ai.google.dev/gemini-api/docs/pricing#gemma-4",
        "checkedAt": "2026-08-07",
    },
)


def read_report(filename: str) -> dict[str, Any]:
    return json.loads((RESULTS / filename).read_text(encoding="utf-8"))


def source_record(filename: str) -> dict[str, str]:
    path = RESULTS / filename
    return {
        "file": filename,
        "href": f"../evaluation-results/{filename}",
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def compact_training(filename: str = "training_log_history.json") -> dict[str, Any]:
    path = FINETUNING / filename
    history = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(history, list):
        raise ValueError("Fine-tuning history must be a JSON list")
    training = [entry for entry in history if "loss" in entry]
    evaluations = [entry for entry in history if "eval_loss" in entry]
    if not training or not evaluations:
        raise ValueError("Fine-tuning history contains no training or evaluation points")

    def evaluation_point(entry: dict[str, Any]) -> dict[str, Any]:
        return {
            "step": int(entry["step"]),
            "epoch": round(float(entry["epoch"]), 4),
            "loss": round(float(entry["eval_loss"]), 4),
            "accuracy": round(float(entry["eval_accuracy"]), 4),
            "precision": round(float(entry["eval_precision"]), 4),
            "recall": round(float(entry["eval_recall"]), 4),
            "f1": round(float(entry["eval_f1"]), 4),
        }

    eval_points = [evaluation_point(entry) for entry in evaluations]
    best = max(eval_points, key=lambda entry: entry["f1"])
    latest = eval_points[-1]
    return {
        "label": "Llama 3.2 1B · QLoRA sequence classifier",
        "adapter": "checkpoint-650",
        "maxStep": max(int(entry["step"]) for entry in history),
        "epoch": round(max(float(entry["epoch"]) for entry in history), 4),
        "training": [
            {
                "step": int(entry["step"]),
                "loss": round(float(entry["loss"]), 4),
                "gradNorm": round(float(entry["grad_norm"]), 4),
                "learningRate": float(entry["learning_rate"]),
            }
            for entry in training
        ],
        "evaluations": eval_points,
        "best": best,
        "latest": latest,
        "source": {
            "file": f"finetuning/{filename}",
            "href": f"../finetuning/{filename}",
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        },
        "note": (
            "Metrics come from the notebook's random 90/10 split. Duplicate and "
            "conflicting prompts have not yet been removed, so these are training "
            "diagnostics rather than final held-out evidence."
        ),
    }


def metric(summary: dict[str, Any], *path: str, fallback: float = 0.0) -> float:
    value: Any = summary
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return float(fallback)
        value = value[key]
    return float(value)


def category_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[(row["configuration"], row["kind"], row["category"])].append(row)
    output: dict[str, dict[str, dict[str, Any]]] = {"attack": {}, "benign": {}}
    for (configuration, kind, category), values in sorted(groups.items()):
        positives = sum(bool(row["breach"] if kind == "attack" else row["blocked"]) for row in values)
        output[kind].setdefault(configuration, {})[category] = {
            "observations": len(values),
            "rate": round(positives / len(values) * 100, 1),
        }
    return output


def compact_run(run_id: str, label: str, filename: str) -> dict[str, Any]:
    report = read_report(filename)
    configs = []
    for config_id in report["configurations"]:
        summary = report["summaries"][config_id]
        prompt_tokens = int(metric(summary, "compute", "prompt_tokens_total"))
        completion_tokens = int(metric(summary, "compute", "completion_tokens_total"))
        input_fpr = metric(
            summary,
            "input_guard",
            "false_positive_rate",
            fallback=metric(summary, "false_positive_rate"),
        )
        configs.append(
            {
                "id": config_id,
                "label": CONFIG_LABELS.get(config_id, config_id),
                "asr": metric(summary, "attack_success_rate"),
                "inputFpr": input_fpr,
                "benignBlock": metric(
                    summary,
                    "end_to_end_benign_block_rate",
                    fallback=metric(summary, "false_positive_rate"),
                ),
                "f1": round(metric(summary, "f1"), 3),
                "meanLatencySeconds": round(metric(summary, "latency_ms", "mean_all") / 1000, 2),
                "modelCalls": int(metric(summary, "compute", "model_calls_total")),
                "promptTokens": prompt_tokens,
                "completionTokens": completion_tokens,
                "tokens": prompt_tokens + completion_tokens,
                "errors": int(metric(summary, "errors")),
                "outputCatches": int(metric(summary, "output_filter", "attack_leaks_caught")),
                "benignOutputCatches": int(metric(summary, "output_filter", "benign_leaks_caught")),
            }
        )
    return {
        "id": run_id,
        "label": label,
        "targetModel": report["target_model"],
        "guardModel": report["guard_models"].get("promptbreak"),
        "createdAt": report["created_at"],
        "dataset": report["dataset"],
        "repeats": report["repeats"],
        "observations": len(report["rows"]),
        "runtimeMinutes": round(report.get("runtime_ms", 0) / 60_000, 1),
        "threshold": report.get("promptbreak_threshold"),
        "repair": report.get("repair"),
        "configs": configs,
        "categories": category_matrix(report["rows"]),
        "source": source_record(filename),
    }


def compact_threshold(run_id: str, label: str, filename: str) -> dict[str, Any]:
    report = read_report(filename)
    by_threshold: dict[float, dict[str, Any]] = defaultdict(dict)
    for summary in report["summaries"]:
        by_threshold[float(summary["threshold"])][summary["mode"]] = summary
    points = []
    for threshold, modes in sorted(by_threshold.items()):
        llm = modes.get("llm_only", {})
        combined = modes.get("heuristic_plus_llm", {})
        points.append(
            {
                "threshold": threshold,
                "llmRecall": round(float(llm.get("attack_recall", 0)) * 100, 1),
                "llmFpr": float(llm.get("false_positive_rate", 0)),
                "combinedRecall": round(float(combined.get("attack_recall", 0)) * 100, 1),
                "combinedFpr": float(combined.get("false_positive_rate", 0)),
            }
        )
    return {
        "runId": run_id,
        "label": label,
        "model": report.get("model"),
        "errors": report.get("errors", 0),
        "points": points,
        "source": source_record(filename),
    }


def compact_attribution(run_id: str, filename: str) -> dict[str, Any]:
    report = read_report(filename)
    return {
        "runId": run_id,
        "benignCases": report["benign_cases"],
        "summary": report["summary"],
        "source": source_record(filename),
    }


def compact_rainbow(run_id: str, label: str, filename: str) -> dict[str, Any]:
    report = read_report(filename)
    archive = report["archive"]
    return {
        "id": run_id,
        "label": label,
        "targetModel": report["target_model"],
        "attackerModel": report["attacker_model"],
        "iterations": report["iterations"],
        "coverage": round(float(archive["coverage"]) * 100, 1),
        "occupied": archive["occupied"],
        "capacity": archive["capacity"],
        "successfulCells": archive["successful_cells"],
        "staticAsr": report["comparison"]["static_seed_asr"],
        "adaptiveAsr": report["comparison"]["adaptive_candidate_asr"],
        "runtimeMinutes": round(report.get("runtime_ms", 0) / 60_000, 1),
        "cells": [
            {
                "family": cell["family"],
                "transformation": cell["transformation"],
                "breach": cell["breach"],
                "blocked": cell["blocked"],
            }
            for cell in archive["cells"]
        ],
        "source": source_record(filename),
    }


def build_dashboard_data() -> dict[str, Any]:
    runs = [compact_run(*spec) for spec in RUN_SPECS]
    thresholds = [compact_threshold(*spec) for spec in THRESHOLD_SPECS]
    attributions = [compact_attribution(*spec) for spec in ATTRIBUTION_SPECS]
    rainbows = [compact_rainbow(*spec) for spec in RAINBOW_SPECS]
    dates = [run["createdAt"] for run in runs]
    return {
        "schemaVersion": "1.0",
        "latestResultAt": max(dates),
        "defaultRun": "qwen27",
        "runs": runs,
        "thresholds": thresholds,
        "attributions": attributions,
        "rainbows": rainbows,
        "training": compact_training(),
        "pricingProfiles": PRICING_PROFILES,
        "defaultPricingByRun": {
            "gemma-original": "gemma4-ai-studio-free",
            "gemma-tuned": "gemma4-ai-studio-free",
            "qwen4": "qwen35-flash-eu-proxy",
            "qwen27": "qwen35-27b-frankfurt",
        },
        "notes": {
            "comparison": (
                "Runs differ in target model, guard model, repetitions, and date. "
                "Treat cross-run comparisons as descriptive, not paired significance tests."
            ),
            "rainbow27": "Qwen 3.5 27B Rainbow-Lite is planned but not yet completed.",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    data = build_dashboard_data()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        "window.PROMPTBREAK_RESULTS = "
        + json.dumps(data, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )
    try:
        display_path = args.output.relative_to(ROOT)
    except ValueError:
        display_path = args.output
    print(f"Wrote {display_path} with {len(data['runs'])} canonical runs")


if __name__ == "__main__":
    main()
