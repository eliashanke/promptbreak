"""Generate compact, dependency-free SVG figures for the ACL report."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / "evaluation-results" / "qwen35-4b-full-guard-comparison-2026-08-07.json"
DEFAULT_OUTPUT = ROOT / "report" / "assets"

INK = "#23373B"
ORANGE = "#EB811B"
ORANGE_DARK = "#C86424"
GREEN = "#557A46"
PURPLE = "#76558B"
BLUE = "#2A7180"
PAPER = "#FAFAFA"
PANEL = "#F1F3F2"
GRID = "#D4DAD7"
MUTED = "#68736F"
WHITE = "#FFFFFF"

LABELS = {
    "prompt_only": "Prompt only",
    "promptbreak_guard": "Promptbreak Guard",
    "llama_guard": "Llama Guard 3",
    "shieldgemma": "ShieldGemma",
    "full_pipeline": "Full Pipeline",
}


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def text(
    x: float,
    y: float,
    value: Any,
    *,
    size: int = 24,
    weight: int = 400,
    fill: str = INK,
    anchor: str = "start",
    rotate: int | None = None,
) -> str:
    transform = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
    return (
        f'<text x="{x}" y="{y}" font-family="Fira Sans, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}"{transform}>{esc(value)}</text>'
    )


def rect(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str,
    stroke: str = "none",
    stroke_width: float = 0,
    radius: float = 0,
) -> str:
    return (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="{radius}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    )


def line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    stroke: str = GRID,
    width: float = 2,
    dash: str | None = None,
) -> str:
    dashed = f' stroke-dasharray="{dash}"' if dash else ""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
        f'stroke="{stroke}" stroke-width="{width}"{dashed}/>'
    )


def circle(cx: float, cy: float, radius: float, *, fill: str) -> str:
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{fill}" '
        f'stroke="{WHITE}" stroke-width="5"/>'
    )


def svg(title: str, body: list[str], *, width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="{esc(title)}">'
        f'{rect(0, 0, width, height, fill=PAPER)}'
        + "".join(body)
        + "</svg>\n"
    )


def heading(title: str, subtitle: str) -> list[str]:
    return [
        text(44, 58, title, size=40, weight=700),
        text(44, 92, subtitle, size=21, fill=MUTED),
    ]


def security_utility(report: dict[str, Any]) -> str:
    body = heading(
        "Security-utility trade-off",
        "Qwen 3.5 4B · 30 cases · lower is better on both axes",
    )
    left, top, plot_w, plot_h = 145, 150, 650, 430
    body.append(rect(left, top, plot_w, plot_h, fill=WHITE, stroke=GRID, stroke_width=2, radius=14))

    for value in (0, 25, 50, 75, 100):
        y = top + plot_h * value / 100
        body.append(line(left, y, left + plot_w, y, dash="7 8"))
        body.append(text(left - 16, y + 7, 100 - value, size=19, fill=MUTED, anchor="end"))
    for value in (0, 5, 10, 15):
        x = left + plot_w * value / 15
        body.append(line(x, top, x, top + plot_h, dash="7 8"))
        body.append(text(x, top + plot_h + 31, value, size=19, fill=MUTED, anchor="middle"))

    body.extend(
        [
            text(left + plot_w / 2, 635, "END-TO-END BENIGN BLOCK RATE (%)", size=18, weight=700, fill=MUTED, anchor="middle"),
            text(67, top + plot_h / 2, "ATTACK SUCCESS RATE (%)", size=18, weight=700, fill=MUTED, anchor="middle", rotate=-90),
            text(left + 18, top + plot_h - 18, "LOWER IS BETTER", size=17, weight=700, fill=GREEN),
        ]
    )

    points = [
        ("prompt_only", "Prompt only + ShieldGemma", 18, 32, INK),
        ("llama_guard", "Llama Guard 3", 18, -10, PURPLE),
        ("promptbreak_guard", "Promptbreak Guard", 18, -10, ORANGE_DARK),
        ("full_pipeline", "Full Pipeline", -18, -42, GREEN),
    ]
    for key, label, dx, dy, color in points:
        summary = report["summaries"][key]
        benign_block = float(summary["end_to_end_benign_block_rate"])
        asr = float(summary["attack_success_rate"])
        x = left + plot_w * benign_block / 15
        y = top + plot_h * (1 - asr / 100)
        body.append(circle(x, y, 14, fill=color))
        anchor = "end" if key == "full_pipeline" else "start"
        body.append(text(x + dx, y + dy, label, size=21, weight=700, anchor=anchor))
        body.append(text(x + dx, y + dy + 25, f"ASR {asr:.1f}% · BR {benign_block:.1f}%", size=17, fill=MUTED, anchor=anchor))
    return svg("Security-utility trade-off", body, width=900, height=680)


def compute_profile(report: dict[str, Any]) -> str:
    body = heading(
        "Cost of protection",
        "Measured local compute proxies · provider API fees were USD 0",
    )
    body.extend(
        [
            text(355, 144, "MEAN LATENCY", size=19, weight=700, fill=MUTED, anchor="middle"),
            text(355, 170, "seconds", size=17, fill=MUTED, anchor="middle"),
            text(700, 144, "TOKEN VOLUME", size=19, weight=700, fill=MUTED, anchor="middle"),
            text(700, 170, "tokens per case", size=17, fill=MUTED, anchor="middle"),
        ]
    )
    configs = report["configurations"]
    max_latency = 8.0
    max_tokens = 600.0
    for index, key in enumerate(configs):
        summary = report["summaries"][key]
        latency = float(summary["latency_ms"]["mean_all"]) / 1000
        compute = summary["compute"]
        tokens = float(compute["tokens_per_case"])
        calls = float(compute["model_calls_per_case"])
        y = 220 + index * 118
        color = GREEN if key == "full_pipeline" else ORANGE
        body.extend(
            [
                text(42, y + 24, LABELS[key], size=22, weight=700),
                text(42, y + 51, f"{calls:.2f} calls/case", size=17, fill=MUTED),
                rect(250, y, 210, 35, fill=PANEL, radius=17),
                rect(250, y, 210 * latency / max_latency, 35, fill=color, radius=17),
                text(472, y + 27, f"{latency:.1f}s", size=19, weight=700),
                rect(590, y, 220, 35, fill=PANEL, radius=17),
                rect(590, y, 220 * tokens / max_tokens, 35, fill=BLUE if key != "full_pipeline" else GREEN, radius=17),
                text(822, y + 27, f"{tokens:.0f}", size=19, weight=700),
            ]
        )
    body.extend(
        [
            rect(42, 814, 816, 82, fill="#F8EFE7", stroke=GRID, stroke_width=2, radius=14),
            text(66, 849, "Interpretation", size=20, weight=700, fill=ORANGE_DARK),
            text(202, 849, "Promptbreak improves security with roughly 2.3× the token volume", size=19, weight=600),
            text(202, 875, "of prompt only; local API cost is zero, but compute cost is not.", size=18, fill=MUTED),
        ]
    )
    return svg("Latency and compute profile", body, width=900, height=930)


def category_rate(rows: list[dict[str, Any]], config: str, category: str, kind: str) -> float:
    selected = [
        row for row in rows
        if row["configuration"] == config and row["category"] == category and row["kind"] == kind
    ]
    key = "breach" if kind == "attack" else "blocked"
    return 100 * sum(bool(row[key]) for row in selected) / len(selected)


def heat_color(value: float) -> str:
    low = (232, 240, 234)
    high = (235, 129, 27)
    ratio = max(0.0, min(1.0, value / 100))
    channels = [round(start + (end - start) * ratio) for start, end in zip(low, high)]
    return "#" + "".join(f"{channel:02X}" for channel in channels)


def heatmap_block(
    body: list[str],
    report: dict[str, Any],
    *,
    y: int,
    title_value: str,
    categories: list[tuple[str, str]],
    kind: str,
) -> None:
    body.append(text(42, y, title_value, size=27, weight=700))
    grid_y = y + 48
    label_w, cell_w, cell_h = 205, (815 - 205) / len(categories), 58
    for column, (_, label) in enumerate(categories):
        x = 42 + label_w + column * cell_w + cell_w / 2
        body.append(text(x, grid_y, label, size=16, weight=700, fill=MUTED, anchor="middle"))
    for row_index, config in enumerate(report["configurations"]):
        cell_y = grid_y + 20 + row_index * cell_h
        body.append(text(42 + label_w - 15, cell_y + 34, LABELS[config], size=18, weight=600, anchor="end"))
        for column, (category, _) in enumerate(categories):
            rate = category_rate(report["rows"], config, category, kind)
            cell_x = 42 + label_w + column * cell_w
            body.append(rect(cell_x, cell_y, cell_w - 5, cell_h - 5, fill=heat_color(rate), stroke=WHITE, stroke_width=2, radius=7))
            body.append(text(cell_x + (cell_w - 5) / 2, cell_y + 34, f"{rate:.0f}%", size=19, weight=700, fill=WHITE if rate >= 70 else INK, anchor="middle"))


def category_heatmaps(report: dict[str, Any]) -> str:
    body = heading(
        "Where defenses fail",
        "Orange indicates an undesirable rate · lower is better",
    )
    heatmap_block(
        body,
        report,
        y=145,
        title_value="Attack success rate by family",
        categories=[
            ("authority", "Authority"),
            ("format_smuggling", "Format"),
            ("multi_turn", "Multi-turn"),
            ("encoding", "Encoding"),
        ],
        kind="attack",
    )
    heatmap_block(
        body,
        report,
        y=545,
        title_value="End-to-end benign block rate by trigger",
        categories=[
            ("debugging", "Debug"),
            ("encoding", "Encoding"),
            ("password", "Password"),
            ("roleplay", "Roleplay"),
            ("system_prompt", "System"),
        ],
        kind="benign",
    )
    body.extend(
        [
            rect(42, 950, 816, 76, fill=PANEL, stroke=GRID, stroke_width=2, radius=14),
            text(66, 983, "Key pattern", size=19, weight=700, fill=ORANGE_DARK),
            text(190, 983, "Promptbreak misses encoding; the Full Pipeline closes that gap.", size=18, weight=600),
            text(190, 1008, "Its two benign output catches occur in password and system-prompt cases.", size=17, fill=MUTED),
        ]
    )
    return svg("Attack and benign category heatmaps", body, width=900, height=1060)


def generate(report_path: Path, output_dir: Path) -> list[Path]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("repeats") != 1 or len(report.get("rows", [])) != 150:
        raise ValueError("Expected the canonical 30 x 5 x 1 Qwen report")
    output_dir.mkdir(parents=True, exist_ok=True)
    figures = {
        "report-security-utility.svg": security_utility(report),
        "report-latency-compute.svg": compute_profile(report),
        "report-category-heatmaps.svg": category_heatmaps(report),
    }
    paths = []
    for filename, content in figures.items():
        path = output_dir / filename
        path.write_text(content, encoding="utf-8")
        paths.append(path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    paths = generate(args.report, args.output_dir)
    print("Wrote " + ", ".join(str(path.relative_to(ROOT)) for path in paths))


if __name__ == "__main__":
    main()
