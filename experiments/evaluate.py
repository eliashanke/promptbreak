"""Run the reproducible benchmark for both defense configurations."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from tqdm import tqdm

from promptbreak.main import DEFAULT_MODEL, LEVEL_BY_ID, run_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate both Promptbreak defenses")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--level", type=int, choices=LEVEL_BY_ID, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    results = []
    for defense in tqdm(
        ("baseline", "guarded"),
        desc="Evaluation",
        unit="configuration",
        dynamic_ncols=True,
    ):
        results.append(run_evaluation(LEVEL_BY_ID[args.level], defense, args.model))
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "level": args.level,
        "model": args.model,
        "results": results,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
