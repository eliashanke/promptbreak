"""Create dependency-free SVG visualizations for the full Promptbreak evaluation."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "evaluation-results"
OUT = RESULTS / "visualizations"
GUARD_REPORT = RESULTS / "full-guard-comparison-2026-07-30.json"
RAINBOW_REPORT = RESULTS / "rainbow-lite-full-pipeline-2026-07-30.json"

TEAL = "#23373B"
ORANGE = "#EB811B"
ORANGE_DARK = "#C86424"
TAN = "#F1E4D7"
PAPER = "#FAFAFA"
PANEL = "#F3F5F5"
GRID = "#D3D8D7"
MUTED = "#596568"
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
    size: int = 18,
    weight: int = 400,
    fill: str = TEAL,
    anchor: str = "start",
    rotate: int | None = None,
    letter_spacing: float | None = None,
) -> str:
    transform = f' transform="rotate({rotate} {x} {y})"' if rotate is not None else ""
    spacing = f' letter-spacing="{letter_spacing}"' if letter_spacing is not None else ""
    return (
        f'<text x="{x}" y="{y}" font-family="Fira Sans, Arial, sans-serif" '
        f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}"{transform}{spacing}>{esc(value)}</text>'
    )


def rect(
    x: float,
    y: float,
    width: float,
    height: float,
    *,
    fill: str = PAPER,
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


def circle(cx: float, cy: float, radius: float, *, fill: str, stroke: str = WHITE) -> str:
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="{fill}" '
        f'stroke="{stroke}" stroke-width="3"/>'
    )


def svg_document(width: int, height: int, body: Iterable[str], title: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">\n'
        f'<rect width="{width}" height="{height}" fill="{PAPER}"/>\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )


def write_svg(name: str, width: int, height: int, body: list[str], title: str) -> None:
    (OUT / name).write_text(svg_document(width, height, body, title), encoding="utf-8")


def category_rate(rows: list[dict[str, Any]], config: str, category: str, kind: str) -> float:
    selected = [
        row
        for row in rows
        if row["configuration"] == config
        and row["category"] == category
        and row["kind"] == kind
    ]
    if not selected:
        return 0.0
    key = "breach" if kind == "attack" else "blocked"
    return sum(bool(row[key]) for row in selected) / len(selected) * 100


def heat_color(value: float) -> str:
    start = (238, 242, 241)
    end = (235, 129, 27)
    ratio = max(0.0, min(1.0, value / 100))
    channels = tuple(round(a + (b - a) * ratio) for a, b in zip(start, end))
    return f"#{channels[0]:02X}{channels[1]:02X}{channels[2]:02X}"


def security_utility(guard: dict[str, Any]) -> None:
    case_count = int(guard["dataset"]["case_count"])
    repeats = int(guard["repeats"])
    repeat_label = "repetition" if repeats == 1 else "repetitions"
    body: list[str] = []
    body += [
        text(70, 70, "Security–utility trade-off", size=38, weight=700),
        text(
            70,
            105,
            f"Evaluation · {case_count} cases × {len(guard['configurations'])} configurations × {repeats} {repeat_label}",
            size=18,
            fill=MUTED,
        ),
        rect(60, 140, 920, 600, fill=WHITE, stroke=GRID, stroke_width=2, radius=24),
    ]
    left, top, plot_w, plot_h = 145, 205, 760, 450
    summaries = guard["summaries"]
    full = summaries["full_pipeline"]
    llama = summaries["llama_guard"]
    shield = summaries["shieldgemma"]
    attacks = full["confusion_matrix"]["tp"] + full["confusion_matrix"]["fn"]
    benign = full["confusion_matrix"]["fp"] + full["confusion_matrix"]["tn"]
    body += [
        rect(left, top + plot_h / 2, plot_w / 2, plot_h / 2, fill=TAN),
        rect(left + plot_w / 2, top + plot_h / 2, plot_w / 2, plot_h / 2, fill=PANEL),
    ]
    for tick in (0, 25, 50, 75, 100):
        x = left + plot_w * tick / 100
        y = top + plot_h * (1 - tick / 100)
        body += [
            line(x, top, x, top + plot_h, dash="7 8"),
            line(left, y, left + plot_w, y, dash="7 8"),
        ]
        if tick in (0, 50, 100):
            body += [
                text(x, top + plot_h + 34, f"{tick}%", size=16, weight=600, fill=MUTED, anchor="middle"),
                text(left - 18, y + 6, f"{tick}%", size=16, weight=600, fill=MUTED, anchor="end"),
            ]
    body += [
        text(left + plot_w / 2, 710, "END-TO-END BENIGN BLOCK RATE → lower is better", size=17, weight=600, fill=MUTED, anchor="middle"),
        text(82, top + plot_h / 2, "ATTACK SUCCESS RATE → lower is better", size=17, weight=600, fill=MUTED, anchor="middle", rotate=-90),
        text(left + plot_w / 2 - 20, top + plot_h - 22, "DESIRED REGION", size=15, weight=700, fill=ORANGE_DARK, anchor="end"),
    ]

    point_styles = {
        "prompt_only": (TEAL, -2, 34),
        "shieldgemma": ("#839093", 18, 60),
        "llama_guard": (ORANGE, 18, -12),
        "promptbreak_guard": (ORANGE_DARK, -12, -24),
        "full_pipeline": (TEAL, -12, -24),
    }
    for config in guard["configurations"]:
        if config == "shieldgemma":
            continue
        summary = summaries[config]
        x = left + plot_w * summary["false_positive_rate"] / 100
        y = top + plot_h * (1 - summary["attack_success_rate"] / 100)
        color, dx, dy = point_styles[config]
        body.append(circle(x, y, 11, fill=color))
        if config == "prompt_only":
            body.append(text(x, y + 5, "2", size=11, weight=700, fill=WHITE, anchor="middle"))
        anchor = "end" if x > left + plot_w * 0.7 else "start"
        label_x = x + dx
        if anchor == "end":
            label_x = x - 18
        else:
            label_x = x + 18
        body += [
            text(
                label_x,
                y + dy,
                "Prompt only + ShieldGemma" if config == "prompt_only" else LABELS[config],
                size=16,
                weight=700,
                anchor=anchor,
            ),
            text(
                label_x,
                y + dy + 22,
                f"ASR {summary['attack_success_rate']:.1f}% · BBR {summary['false_positive_rate']:.1f}%",
                size=14,
                fill=MUTED,
                anchor=anchor,
            ),
        ]

    body += [
        rect(1020, 140, 520, 600, fill=PANEL, stroke=GRID, stroke_width=2, radius=24),
        text(1060, 190, "WHAT THE RUN SHOWS", size=16, weight=700, fill=ORANGE_DARK, letter_spacing=1.2),
        text(1060, 250, "Full Pipeline", size=25, weight=700),
        text(1060, 283, f"{round(attacks * full['attack_success_rate'] / 100)} / {attacks} attacks succeed", size=19, weight=600),
        text(1060, 313, f"{full['confusion_matrix']['fp']} / {benign} benign cases are blocked", size=18, fill=MUTED),
        line(1060, 350, 1500, 350),
        text(1060, 405, "Llama Guard 3", size=25, weight=700),
        text(1060, 438, f"{round(attacks * llama['attack_success_rate'] / 100)} / {attacks} attacks succeed", size=19, weight=600),
        text(1060, 468, f"{llama['confusion_matrix']['fp']} / {benign} benign cases are blocked", size=18, fill=MUTED),
        line(1060, 505, 1500, 505),
        text(1060, 560, "ShieldGemma", size=25, weight=700),
        text(1060, 593, f"{round(attacks * shield['attack_success_rate'] / 100)} / {attacks} attacks succeed", size=19, weight=600),
        text(1060, 623, f"{shield['confusion_matrix']['fp']} / {benign} benign cases are blocked", size=18, fill=MUTED),
        rect(1050, 660, 460, 52, fill=TAN, radius=12),
        text(1280, 694, "No configuration reaches the desired region.", size=17, weight=700, anchor="middle"),
    ]
    write_svg("security-utility.svg", 1600, 800, body, "Security and utility trade-off")


def category_heatmaps(guard: dict[str, Any]) -> None:
    rows = guard["rows"]
    configs = guard["configurations"]
    attack_categories = ["authority", "format_smuggling", "multi_turn", "encoding"]
    benign_categories = ["debugging", "encoding", "password", "roleplay", "system_prompt"]
    body: list[str] = [
        text(70, 70, "Where each guard succeeds—and fails", size=38, weight=700),
        text(70, 105, f"Rates aggregated across {guard['repeats']} " + ("repetition" if guard["repeats"] == 1 else "repetitions"), size=18, fill=MUTED),
    ]

    def draw_heatmap(
        y0: int,
        title_value: str,
        subtitle: str,
        categories: list[str],
        kind: str,
    ) -> None:
        body.extend(
            [
                text(70, y0, title_value, size=25, weight=700),
                text(70, y0 + 29, subtitle, size=16, fill=MUTED),
            ]
        )
        label_w, cell_w, cell_h = 250, 220, 58
        grid_x, grid_y = 70, y0 + 70
        for col, category in enumerate(categories):
            display = category.replace("_", " ").title()
            body.append(text(grid_x + label_w + col * cell_w + cell_w / 2, grid_y - 18, display, size=15, weight=700, anchor="middle"))
        for row_idx, config in enumerate(configs):
            y = grid_y + row_idx * cell_h
            body.append(text(grid_x + label_w - 20, y + 37, LABELS[config], size=17, weight=600, anchor="end"))
            for col, category in enumerate(categories):
                rate = category_rate(rows, config, category, kind)
                x = grid_x + label_w + col * cell_w
                fill = heat_color(rate)
                body.append(rect(x, y, cell_w - 8, cell_h - 8, fill=fill, stroke=WHITE, stroke_width=2, radius=8))
                text_fill = WHITE if rate >= 70 else TEAL
                body.append(text(x + (cell_w - 8) / 2, y + 34, f"{rate:.0f}%", size=18, weight=700, fill=text_fill, anchor="middle"))

    draw_heatmap(
        165,
        "Attack success rate by family",
        "100% means every attack in that family leaked the secret.",
        attack_categories,
        "attack",
    )
    draw_heatmap(
        575,
        "End-to-end benign block rate by trigger type",
        "Includes input refusals and target-model leaks caught by output filters.",
        benign_categories,
        "benign",
    )
    body += [
        rect(70, 985, 1460, 75, fill=PANEL, stroke=GRID, stroke_width=2, radius=16),
        text(100, 1018, "Pattern:", size=18, weight=700, fill=ORANGE_DARK),
        text(190, 1018, "Category detail exposes differences that aggregate ASR and benign-block rates can hide.", size=18, weight=600),
        text(190, 1045, "Interpret these rates only within the fixed, application-specific evaluation set.", size=17, fill=MUTED),
    ]
    write_svg("category-heatmaps.svg", 1600, 1120, body, "Attack and benign category heatmaps")


def cost_latency(guard: dict[str, Any]) -> None:
    summaries = guard["summaries"]
    configs = guard["configurations"]
    body: list[str] = [
        text(70, 70, "Latency and computational cost", size=38, weight=700),
        text(70, 105, "Local API cost is €0; wall-clock time, calls, and tokens are the useful proxies.", size=18, fill=MUTED),
    ]
    observations = int(guard["dataset"]["case_count"]) * int(guard["repeats"])
    panel_specs = [
        ("Warm latency", "p95 bar · p50 marker", lambda s: s["latency_ms"]["p95_warm"] / 1000, lambda s: s["latency_ms"]["p50_warm"] / 1000, "s"),
        ("Model calls", f"total across {observations} observations", lambda s: s["compute"]["model_calls_total"], None, ""),
        ("Tokens per case", "prompt + completion", lambda s: s["compute"]["tokens_per_case"], None, ""),
    ]
    panels = [
        (*spec[:4], max(1.0, max(float(spec[2](summaries[c])) for c in configs) * 1.1), spec[4])
        for spec in panel_specs
    ]
    for panel_idx, (title_value, subtitle, value_fn, marker_fn, max_value, suffix) in enumerate(panels):
        x0 = 55 + panel_idx * 515
        body += [
            rect(x0, 145, 480, 650, fill=WHITE, stroke=GRID, stroke_width=2, radius=22),
            text(x0 + 28, 190, title_value, size=24, weight=700),
            text(x0 + 28, 218, subtitle, size=15, fill=MUTED),
        ]
        for idx, config in enumerate(configs):
            y = 275 + idx * 95
            value = float(value_fn(summaries[config]))
            bar_w = 300 * value / max_value
            body += [
                text(x0 + 28, y, LABELS[config], size=16, weight=600),
                rect(x0 + 28, y + 18, 300, 22, fill=PANEL, radius=11),
                rect(x0 + 28, y + 18, bar_w, 22, fill=ORANGE if config != "full_pipeline" else TEAL, radius=11),
                text(x0 + 350, y + 36, f"{value:.1f}{suffix}", size=17, weight=700),
            ]
            if marker_fn:
                marker = float(marker_fn(summaries[config]))
                marker_x = x0 + 28 + 300 * marker / max_value
                body += [
                    line(marker_x, y + 14, marker_x, y + 44, stroke=TEAL, width=3),
                    text(marker_x, y + 60, f"p50 {marker:.1f}s", size=12, fill=MUTED, anchor="middle"),
                ]
    body += [
        rect(70, 835, 1460, 85, fill=TAN, radius=16),
        text(100, 870, "Interpretation:", size=18, weight=700, fill=ORANGE_DARK),
        text(235, 870, "Compare guard-refusal, deterministic legacy, and target-model paths before interpreting end-to-end latency.", size=18, weight=600),
        text(235, 900, "Early blocking can reduce latency, while allowed prompts include both guard and target inference.", size=17, fill=MUTED),
    ]
    write_svg("latency-compute.svg", 1600, 970, body, "Latency and computational cost")


def rainbow_archive(rainbow: dict[str, Any]) -> None:
    archive = rainbow["archive"]
    cell_lookup = {
        (cell["family"], cell["transformation"]): cell
        for cell in archive["cells"]
    }
    families = archive["dimensions"]["attack_family"]
    transformations = archive["dimensions"]["transformation"]
    body: list[str] = [
        text(70, 70, "Rainbow-Lite: explored diversity, no successful breach", size=38, weight=700),
        text(70, 105, f"Full Pipeline · 4 static seeds + {rainbow['iterations']} adaptive mutations", size=18, fill=MUTED),
        rect(60, 145, 1040, 610, fill=WHITE, stroke=GRID, stroke_width=2, radius=22),
    ]
    grid_x, grid_y, cell_w, cell_h = 270, 235, 195, 105
    for col, transformation in enumerate(transformations):
        body.append(text(grid_x + col * cell_w + 87, grid_y - 24, transformation.title(), size=16, weight=700, anchor="middle"))
    for row_idx, family in enumerate(families):
        y = grid_y + row_idx * cell_h
        body.append(text(grid_x - 24, y + 56, family.replace("_", " ").title(), size=17, weight=600, anchor="end"))
        for col, transformation in enumerate(transformations):
            x = grid_x + col * cell_w
            cell = cell_lookup.get((family, transformation))
            if cell is None:
                body += [
                    rect(x, y, cell_w - 12, cell_h - 12, fill=PANEL, stroke=GRID, stroke_width=2, radius=12),
                    text(x + 90, y + 43, "not tested", size=15, fill=MUTED, anchor="middle"),
                    text(x + 90, y + 67, f"within k = {rainbow['iterations']}", size=13, fill=MUTED, anchor="middle"),
                ]
            else:
                is_seed = cell["source"] == "seed"
                body += [
                    rect(x, y, cell_w - 12, cell_h - 12, fill=TEAL if is_seed else TAN, stroke=GRID, stroke_width=2, radius=12),
                    text(x + 90, y + 38, "BLOCKED", size=16, weight=700, fill=WHITE if is_seed else TEAL, anchor="middle"),
                    text(
                        x + 90,
                        y + 65,
                        "seed" if is_seed else f"novelty {cell['fitness']['novelty']:.2f}",
                        size=14,
                        fill=WHITE if is_seed else MUTED,
                        anchor="middle",
                    ),
                ]
    body += [
        rect(1140, 145, 400, 610, fill=PANEL, stroke=GRID, stroke_width=2, radius=22),
        text(1180, 195, "ARCHIVE SUMMARY", size=16, weight=700, fill=ORANGE_DARK, letter_spacing=1.2),
        text(1180, 265, f"{archive['coverage'] * 100:.0f}%", size=46, weight=700),
        text(1300, 258, "coverage", size=20, weight=700),
        text(1180, 300, f"{archive['occupied']} of {archive['capacity']} cells occupied", size=17, fill=MUTED),
        line(1180, 335, 1500, 335),
        text(1180, 395, f"{rainbow['comparison']['adaptive_candidate_asr']:.0f}%", size=46, weight=700),
        text(1300, 388, "adaptive ASR", size=20, weight=700),
        text(1180, 430, f"{sum(bool(event.get('breach')) for event in rainbow['events'] if event.get('iteration', 0) > 0)} of {rainbow['iterations']} mutations breached", size=17, fill=MUTED),
        line(1180, 465, 1500, 465),
        text(1180, 525, archive["successful_cells"], size=46, weight=700),
        text(1230, 518, "successful cells", size=20, weight=700),
        text(1180, 560, f"Seed ASR: {rainbow['comparison']['static_seed_asr']:.0f}%", size=17, fill=MUTED),
        rect(1170, 610, 340, 105, fill=TAN, radius=14),
        text(1195, 645, "Important:", size=17, weight=700, fill=ORANGE_DARK),
        text(1195, 674, "Coverage measures explored cells;", size=16, weight=600),
        text(1195, 698, "it does not imply general robustness.", size=16, weight=600),
    ]
    write_svg("rainbow-lite.svg", 1600, 820, body, "Rainbow-Lite archive")


def gallery(guard: dict[str, Any], rainbow: dict[str, Any]) -> None:
    cards = [
        ("security-utility.svg", "Security–utility trade-off"),
        ("category-heatmaps.svg", "Category-level behavior"),
        ("latency-compute.svg", "Latency and compute"),
        ("rainbow-lite.svg", "Rainbow-Lite archive"),
    ]
    markup = "\n".join(
        f'<section><h2>{esc(title)}</h2><img src="{esc(file)}" alt="{esc(title)}"></section>'
        for file, title in cards
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Promptbreak evaluation visualizations</title>
  <style>
    :root {{ color: {TEAL}; background: #ecefed; font-family: "Fira Sans", Arial, sans-serif; }}
    body {{ max-width: 1500px; margin: 0 auto; padding: 32px; }}
    h1 {{ margin: 0 0 8px; }} p {{ color: {MUTED}; margin: 0 0 28px; }}
    section {{ background: {PAPER}; border: 1px solid {GRID}; border-radius: 16px; padding: 18px; margin: 0 0 28px; }}
    h2 {{ margin: 0 0 14px; font-size: 20px; }}
    img {{ display: block; width: 100%; height: auto; }}
  </style>
</head>
<body>
  <h1>Promptbreak evaluation</h1>
  <p>{guard['dataset']['case_count'] * len(guard['configurations']) * guard['repeats']} static observations plus a {rainbow['iterations']}-iteration Rainbow-Lite run.</p>
  {markup}
</body>
</html>
"""
    (OUT / "index.html").write_text(document, encoding="utf-8")


def main() -> None:
    global OUT
    parser = argparse.ArgumentParser(description="Render Promptbreak result JSONs as SVG")
    parser.add_argument("--guard-report", type=Path, default=GUARD_REPORT)
    parser.add_argument("--rainbow-report", type=Path, default=RAINBOW_REPORT)
    parser.add_argument("--output-dir", type=Path, default=OUT)
    args = parser.parse_args()
    guard = json.loads(args.guard_report.read_text(encoding="utf-8"))
    rainbow = json.loads(args.rainbow_report.read_text(encoding="utf-8"))
    OUT = args.output_dir
    OUT.mkdir(parents=True, exist_ok=True)
    security_utility(guard)
    category_heatmaps(guard)
    cost_latency(guard)
    rainbow_archive(rainbow)
    gallery(guard, rainbow)
    print(f"Wrote visualizations to {OUT}")


if __name__ == "__main__":
    main()
