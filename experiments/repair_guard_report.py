"""Replace failed guard observations with verified reruns and resummarize a report."""

from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from experiments.compare_guards import summarize_rows


def row_key(row: dict[str, Any]) -> tuple[str, int, str]:
    return str(row["configuration"]), int(row["repetition"]), str(row["case_id"])


def repair_report(
    base: dict[str, Any],
    patch: dict[str, Any],
    *,
    base_name: str,
    patch_name: str,
) -> dict[str, Any]:
    base_dataset = base.get("dataset", {})
    patch_dataset = patch.get("dataset", {})
    for field in ("name", "version"):
        if base_dataset.get(field) != patch_dataset.get(field):
            raise ValueError(f"Report mismatch in dataset.{field}")
    for field in ("target_model", "guard_models", "promptbreak_threshold", "repeats"):
        if base.get(field) != patch.get(field):
            raise ValueError(f"Report mismatch in {field}")

    base_rows = base.get("rows")
    patch_rows = patch.get("rows")
    if not isinstance(base_rows, list) or not isinstance(patch_rows, list):
        raise ValueError("Both reports must contain rows")
    replacements = {row_key(row): row for row in patch_rows}
    failed_keys = [row_key(row) for row in base_rows if row.get("guard_error")]
    if not failed_keys:
        raise ValueError("Base report contains no guard errors to repair")
    missing = [key for key in failed_keys if key not in replacements]
    if missing:
        raise ValueError(f"Patch report is missing failed observations: {missing}")
    still_failed = [key for key in failed_keys if replacements[key].get("guard_error")]
    if still_failed:
        raise ValueError(f"Patch observations still contain guard errors: {still_failed}")

    repaired = deepcopy(base)
    repaired["rows"] = [
        deepcopy(replacements[row_key(row)]) if row_key(row) in failed_keys else row
        for row in base_rows
    ]
    configurations = repaired["configurations"]
    repaired["summaries"] = {
        configuration: summarize_rows(
            [row for row in repaired["rows"] if row["configuration"] == configuration]
        )
        for configuration in configurations
    }
    repaired["runtime_ms"] = int(base.get("runtime_ms", 0)) + int(patch.get("runtime_ms", 0))
    repaired["repair"] = {
        "repaired_at": datetime.now(timezone.utc).isoformat(),
        "base_report": base_name,
        "patch_report": patch_name,
        "replaced_observations": len(failed_keys),
        "criterion": "Only rows with a non-empty guard_error were replaced.",
        "reason": "Qwen returned valid JSON inside an exact Markdown code fence.",
    }
    return repaired


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = repair_report(
        json.loads(args.base.read_text(encoding="utf-8")),
        json.loads(args.patch.read_text(encoding="utf-8")),
        base_name=args.base.name,
        patch_name=args.patch.name,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["repair"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
