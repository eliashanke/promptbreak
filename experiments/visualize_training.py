"""Generate report-ready SVG diagnostics from the fine-tuning log."""

from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = ROOT / "finetuning" / "training_log_history.json"
DEFAULT_OUTPUT = ROOT / "report" / "assets"

INK = "#23373B"
ORANGE = "#EB811B"
BLUE = "#2A7180"
GREEN = "#557A46"
PURPLE = "#76558B"
PAPER = "#FAFAFA"
PANEL = "#F1F3F2"
GRID = "#D4DAD7"
MUTED = "#68736F"


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def text(x: float, y: float, value: Any, *, size: int = 18, weight: int = 400,
         fill: str = INK, anchor: str = "start") -> str:
    return (
        f'<text x="{x}" y="{y}" font-family="Fira Sans, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}">{esc(value)}</text>'
    )


def base_svg(title: str, subtitle: str, body: str, *, width: int = 1400,
             height: int = 720) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" fill="{PAPER}"/>'
        f'{text(60, 62, title, size=40, weight=700)}'
        f'{text(60, 96, subtitle, size=22, fill=MUTED)}'
        f'{body}</svg>\n'
    )


def chart(
    series: list[dict[str, Any]],
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    title: str,
    y_min: float,
    y_max: float,
    y_format: Callable[[float], str],
    log_y: bool = False,
) -> str:
    left, right, top, bottom = 64, 20, 55, 55
    plot_x, plot_y = x + left, y + top
    plot_w, plot_h = width - left - right, height - top - bottom
    points = [point for item in series for point in item["points"]]
    x_min = min(float(point["step"]) for point in points)
    x_max = max(float(point["step"]) for point in points)

    def scale_x(value: float) -> float:
        return plot_x + (value - x_min) / max(x_max - x_min, 1) * plot_w

    if log_y:
        log_min, log_max = math.log10(y_min), math.log10(y_max)

        def scale_y(value: float) -> float:
            normalized = (math.log10(max(value, y_min)) - log_min) / (log_max - log_min)
            return plot_y + (1 - normalized) * plot_h
    else:
        def scale_y(value: float) -> float:
            normalized = (value - y_min) / (y_max - y_min)
            return plot_y + (1 - normalized) * plot_h

    output = [
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="5" fill="{PANEL}"/>',
        text(x + 24, y + 36, title, size=28, weight=700),
    ]
    for index in range(5):
        ratio = index / 4
        value = 10 ** (math.log10(y_min) + ratio * (math.log10(y_max) - math.log10(y_min))) if log_y else y_min + ratio * (y_max - y_min)
        py = scale_y(value)
        output.append(f'<line x1="{plot_x}" y1="{py}" x2="{plot_x + plot_w}" y2="{py}" stroke="{GRID}"/>')
        output.append(text(plot_x - 10, py + 7, y_format(value), size=21, fill=MUTED, anchor="end"))
    for index in range(5):
        ratio = index / 4
        value = round(x_min + ratio * (x_max - x_min))
        px = scale_x(value)
        output.append(text(px, plot_y + plot_h + 30, value, size=21, fill=MUTED, anchor="middle"))
    output.append(text(plot_x + plot_w, plot_y + plot_h + 51, "TRAINING STEP", size=17, fill=MUTED, anchor="end"))

    legend_x = x + width - 24
    for index, item in enumerate(reversed(series)):
        label_y = y + 31
        label_width = max(110, len(item["label"]) * 11 + 38)
        legend_x -= label_width
        output.append(f'<line x1="{legend_x}" y1="{label_y - 5}" x2="{legend_x + 18}" y2="{label_y - 5}" stroke="{item["color"]}" stroke-width="4"/>')
        output.append(text(legend_x + 25, label_y + 2, item["label"], size=19, fill=MUTED))

    for item in series:
        coordinates = " ".join(
            f'{scale_x(float(point["step"])):.1f},{scale_y(float(point["value"])):.1f}'
            for point in item["points"]
        )
        output.append(
            f'<polyline points="{coordinates}" fill="none" stroke="{item["color"]}" '
            'stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        for point in item["points"]:
            output.append(
                f'<circle cx="{scale_x(float(point["step"])):.1f}" '
                f'cy="{scale_y(float(point["value"])):.1f}" r="3.5" '
                f'fill="{PAPER}" stroke="{item["color"]}" stroke-width="2"/>'
            )
    return "".join(output)


def validation_figure(evaluations: list[dict[str, Any]]) -> str:
    quality_series = [
        {"label": "F1", "color": ORANGE, "points": [{"step": row["step"], "value": row["eval_f1"]} for row in evaluations]},
        {"label": "Precision", "color": BLUE, "points": [{"step": row["step"], "value": row["eval_precision"]} for row in evaluations]},
        {"label": "Recall", "color": GREEN, "points": [{"step": row["step"], "value": row["eval_recall"]} for row in evaluations]},
        {"label": "Accuracy", "color": PURPLE, "points": [{"step": row["step"], "value": row["eval_accuracy"]} for row in evaluations]},
    ]
    loss_series = [
        {"label": "Validation loss", "color": ORANGE, "points": [{"step": row["step"], "value": row["eval_loss"]} for row in evaluations]},
    ]
    body = chart(
        quality_series, x=50, y=125, width=825, height=540,
        title="Classification quality", y_min=0, y_max=1,
        y_format=lambda value: f"{value:.2f}",
    )
    body += chart(
        loss_series, x=895, y=125, width=455, height=540,
        title="Validation loss", y_min=0, y_max=0.8,
        y_format=lambda value: f"{value:.1f}",
    )
    return base_svg(
        "Fine-tuned guard: validation trajectory",
        "Random stratified 90/10 split · 13 evaluations · higher quality is better, lower loss is better",
        body,
    )


def optimization_figure(training: list[dict[str, Any]], evaluations: list[dict[str, Any]]) -> str:
    loss_series = [
        {"label": "Training loss", "color": ORANGE, "points": [{"step": row["step"], "value": row["loss"]} for row in training]},
        {"label": "Validation loss", "color": BLUE, "points": [{"step": row["step"], "value": row["eval_loss"]} for row in evaluations]},
    ]
    gradient_series = [
        {"label": "Gradient norm", "color": PURPLE, "points": [{"step": row["step"], "value": row["grad_norm"]} for row in training]},
    ]
    body = chart(
        loss_series, x=50, y=125, width=825, height=540,
        title="Training and validation loss", y_min=0, y_max=8.5,
        y_format=lambda value: f"{value:.1f}",
    )
    body += chart(
        gradient_series, x=895, y=125, width=455, height=540,
        title="Gradient norm (log scale)", y_min=0.005, y_max=200,
        y_format=lambda value: f"{value:.2g}", log_y=True,
    )
    return base_svg(
        "Fine-tuned guard: optimization diagnostics",
        "Partial run through step 700 (0.162 epochs) · training values are 10-step logging averages",
        body,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    history = json.loads(args.log.read_text(encoding="utf-8"))
    training = [row for row in history if "loss" in row]
    evaluations = [row for row in history if "eval_loss" in row]
    if not training or not evaluations:
        raise ValueError("Training log must contain training and evaluation entries")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "finetuning-validation.svg").write_text(
        validation_figure(evaluations), encoding="utf-8"
    )
    (args.output_dir / "finetuning-optimization.svg").write_text(
        optimization_figure(training, evaluations), encoding="utf-8"
    )
    print(f"Wrote 2 SVG figures to {args.output_dir.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
