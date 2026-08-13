# Promptbreak – Prompt Injection Escape Room

An interactive red-team game for the NLP in Industry seminar. In each level, a
local language model protects a secret while players try to extract it through
prompt injection. Two defense architectures can be compared directly and
evaluated with a built-in test set.

Everything runs locally through [Ollama](https://ollama.com/). No API keys,
cloud calls, or usage-based costs are required.

## Prototype features

- three increasingly difficult attack scenarios with separate secrets: Level 1
  deliberately contains an easy-to-find legacy QA flaw, Level 2 a narrowly
  defined unsafe SQL export path, and Level 3 a stateful three-stage disaster
  recovery flaw
- **Baseline:** protection through a system prompt only
- **Guarded:** a separate LLM input classifier, heuristic rules, and a
  deterministic output filter
- a challenging guarded bypass in Level 3 involving multi-turn state, a flawed
  legacy allowlist, and Base64 exfiltration
- a local chat UI with model selection, hints, and separate conversation
  histories
- an integrated attack playbook with explained methods and loadable payloads
- a defense trace for every response and an animated breach finale
- a **Defense Builder** with six individually configurable layers and five
  presets
- an **Auto Red-Team Agent** that executes seed attacks and uses Ollama to
  analyze and mutate failed attempts
- a **Benchmark Heatmap** comparing prompt-only, input-guard, output-filter,
  and full-pipeline configurations by ASR, false-positive rate, and latency
- live metrics for attack success rate, blocks, and latency
- a reproducible 30-case study with 15 attacks and 15 benign, XSTest-inspired
  contrast cases
- local comparison adapters for Promptbreak Guard, Llama Guard 3, and
  ShieldGemma
- Ollama telemetry for model calls, tokens, load time, and inference time
- **Rainbow-lite**, a small quality-diversity archive for adaptive attacks
- only one small Python dependency: `tqdm` for progress bars and ETA

## Model selection

The default is `gemma4:latest` because it is already installed on the target
machine and natively supports system prompts, which is particularly useful for
a prompt-injection comparison. Gemma 4 is the current model generation; users
with less memory can use Gemma 3 instead.

| Hardware     | Recommendation  |  Download size | Notes                                   |
| ------------ | --------------- | -------------: | --------------------------------------- |
| 8 GB RAM     | `gemma3:1b`     | approx. 815 MB | fast, but considerably easier to bypass |
| 16 GB RAM    | `gemma3:4b`     | approx. 3.3 GB | compact fallback                        |
| 16–24 GB RAM | `gemma4:latest` | approx. 9.6 GB | **default on the target machine**       |
| 24+ GB RAM   | `gemma4:12b`    | approx. 7.6 GB | current generation, longer context      |

Sizes are taken from the official Ollama pages for
[Gemma 4](https://ollama.com/library/gemma4) and
[Gemma 3](https://ollama.com/library/gemma3). The guard classifier requests
structured output through Ollama's JSON Schema support.

### Chinese comparison models

For a cross-origin comparison, `promptbreak/model_adapters.py` defines short aliases for
several Chinese Ollama models. Download size is only a rough hardware proxy;
parameter count, quantization, and architecture are not directly comparable.
Information current as of July 31, 2026.

| Alias             | Ollama tag        | Download | Context | Use                                |
| ----------------- | ----------------- | -------: | ------: | ---------------------------------- |
| `qwen35_4b`       | `qwen3.5:4b`      |   3.4 GB |    256K | memory-efficient tested comparison |
| `qwen35_9b`       | `qwen3.5:9b`      |   6.6 GB |    256K | modern primary comparison          |
| `qwen3_14b`       | `qwen3:14b`       |   9.3 GB |     40K | closest download-size match        |
| `deepseek_r1_14b` | `deepseek-r1:14b` |   9.0 GB |    128K | reasoning-oriented comparison      |
| `glm4_9b`         | `glm4:9b`         |   5.5 GB |    128K | optional older comparison          |

Sources: [Qwen 3.5](https://ollama.com/library/qwen3.5),
[Qwen 3](https://ollama.com/library/qwen3),
[DeepSeek R1](https://ollama.com/library/deepseek-r1), and
[GLM-4](https://ollama.com/library/glm4). The adapter disables optional
thinking for Qwen and DeepSeek during evaluation so that latency and token use
are not distorted by reasoning traces of different lengths. Any other Ollama
tag can still be supplied directly.

### Experimental fine-tuned Llama guard

[`finetuning/overfiltering.ipynb`](finetuning/overfiltering.ipynb) contains an
experimental binary Llama sequence classifier trained to distinguish benign
prompts (`0`) from prompt injections (`1`). It uses 4-bit NF4 loading and LoRA
adapters on the attention projections. The accompanying
[`data/finetuning/train.json`](data/finetuning/train.json) contains
76,735 examples from 22 named sources: 61,069 benign prompts and 15,666
injections. The 41 MB dataset is stored with Git LFS; run `git lfs pull` after
cloning if it was not downloaded automatically.

The experiment is based on the open-source training corpus and overdefense
motivation of [PIGuard](https://github.com/leolee99/PIGuard/tree/main) and its
[ACL 2025 paper](https://aclanthology.org/2025.acl-long.1468/), but it is not a
PIGuard reproduction. The published PIGuard model uses DeBERTa and the
Mitigating Over-defense for Free (MOF) procedure; the notebook instead adapts a
Llama classifier with QLoRA and does not implement MOF's token-wise bias check
or synthetic benign-data generation.

The notebook has produced a local checkpoint and a versioned training log. Its
best recorded validation F1 is 0.9382 at step 600, but the dataset still
contains duplicate, empty, and conflicting records that must be resolved before
a leakage-safe split is made. These values are training diagnostics, not final
held-out evidence.
The report figures can be regenerated with
`uv run python -m experiments.visualize_training`. Compact security, utility,
category, latency, and compute figures for the report are generated with
`uv run python -m experiments.visualize_report_results`.
See [`FINE_TUNING.md`](FINE_TUNING.md) for the implementation inventory,
reproducibility requirements, attribution wording, and proposed evaluation.

## Quick start

Requirements: Python 3.10+ and [Ollama](https://docs.ollama.com/macos) on macOS,
Linux, or Windows.

```bash
cd project
uv sync
ollama pull gemma4
uv run python -m promptbreak
```

To use the fine-tuned PyTorch guard or run the notebook, install the optional
dependency group and select **Fine-tuned Llama guard** in the app:

```bash
uv sync --group finetuning
uv run python -m promptbreak
```

The local `finetuning/checkpoint-*` directories are generated artifacts and are
not stored in Git. A clean clone therefore needs a separately distributed
adapter (or a new training run) plus access to the gated
`meta-llama/Llama-3.2-1B` base model before this option can load. The standard
Ollama-backed application does not require Hugging Face access.

Then open <http://127.0.0.1:8000>. If the Ollama application is not already
running:

```bash
ollama serve
```

Select a different model in the UI or set it at startup:

```bash
OLLAMA_MODEL=gemma3:4b python3 -m promptbreak --port 8000
```

To use a different Ollama server:

```bash
OLLAMA_URL=http://127.0.0.1:11434 python3 -m promptbreak
```

## Complete reproducible workflow

The following commands run tests, the static comparison, false-positive
diagnosis, Rainbow-lite, and visualizations in the intended order. Run all
commands from `project/`.

### 1. Prepare the environment and models

```bash
uv sync
ollama pull gemma4:latest
ollama pull llama-guard3:1b
ollama pull shieldgemma:2b
ollama list
```

If Ollama is not already running:

```bash
ollama serve
```

### 2. Run the tests

```bash
uv run python -m unittest discover -s tests -v
```

### 3. Validate the benchmark matrix without model calls

```bash
uv run python -m experiments.compare_guards \
  --target-model gemma4:latest \
  --repeats 3 \
  --dry-run
```

The expected matrix contains 30 cases, five configurations, and three repeats,
for a total of 450 case-configuration observations.

### 4. Run an optional short smoke test

```bash
uv run python -m experiments.compare_guards \
  --target-model gemma4:latest \
  --repeats 1 \
  --max-cases 4 \
  --output evaluation-results/smoke-guards.json
```

### 5. Run the full guard comparison

```bash
uv run python -m experiments.compare_guards \
  --target-model gemma4:latest \
  --promptbreak-model gemma4:latest \
  --llama-guard-model llama-guard3:1b \
  --shieldgemma-model shieldgemma:2b \
  --repeats 3 \
  --output evaluation-results/full-guard-comparison.json
```

On the machine used for the seminar, a complete run took approximately 67
minutes. Actual runtime depends on hardware, the model cache, and how many cases
are blocked early.

### 6. Attribute false positives from the Promptbreak Input Guard

```bash
uv run python -m experiments.diagnose_false_positives \
  --model gemma4:latest \
  --output evaluation-results/false-positive-attribution.json
```

The runner tests all 15 benign cases separately against the regex heuristics and
the Gemma classifier without heuristics. Each case is attributed to
`heuristics_only`, `llm_only`, `both`, or `neither`.

### 7. Sweep the confidence threshold

```bash
uv run python -m experiments.sweep_guard_thresholds \
  --model gemma4:latest \
  --output evaluation-results/guard-threshold-sweep.json
```

Each of the 30 prompts is classified exactly once at temperature 0. Thresholds
are then evaluated offline on the same raw decisions, avoiding confounding from
different model outputs.

Run a targeted end-to-end validation of the revised guard with:

```bash
uv run python -m experiments.compare_guards \
  --target-model gemma4:latest \
  --promptbreak-model gemma4:latest \
  --promptbreak-threshold 0.55 \
  --config promptbreak_guard \
  --config full_pipeline \
  --repeats 1 \
  --output evaluation-results/tuned-guard-validation.json
```

### 8. Run Rainbow-lite

The default run generates 24 adaptive candidates. Each of the twelve
non-direct archive cells is visited twice, while successful or more advanced
candidates become parents of later mutations.

```bash
uv run python -m experiments.rainbow_lite \
  --target-model gemma4:latest \
  --attacker-model qwen35_4b \
  --configuration full_pipeline \
  --iterations 24 \
  --output evaluation-results/rainbow-lite-qwen35-4b-24.json
```

Four mutations are sufficient for a quick technical smoke test:

```bash
uv run python -m experiments.rainbow_lite \
  --target-model gemma4:latest \
  --attacker-model qwen35_4b \
  --configuration full_pipeline \
  --iterations 4 \
  --output evaluation-results/rainbow-lite-qwen35-4b-smoke.json
```

The defense filter and objective judge are separate. The filter recognizes the
application's supported direct, hexadecimal, ROT13, reverse, and Base64 leaks.
The stronger judge additionally detects decimal, binary, and Unicode-code-point
outputs. If both components were identical, a measurable full-pipeline bypass
would be impossible by definition.

### 9. Generate visualizations

With no arguments, the visualization script reads the historical full reports.
Any dated guard and Rainbow reports can be rendered to a separate output
directory:

```bash
uv run python -m experiments.visualize_results \
  --guard-report evaluation-results/qwen35-4b-full-guard-comparison-2026-08-07.json \
  --rainbow-report evaluation-results/rainbow-lite-qwen35-4b-24-2026-08-07.json \
  --output-dir evaluation-results/visualizations/qwen35-4b-2026-08-07
```

This creates SVG files and an HTML overview in
`evaluation-results/visualizations/`. PNG files can optionally be generated
with `rsvg-convert` from `librsvg`:

```bash
for file in evaluation-results/visualizations/*.svg; do
  rsvg-convert -w 1600 "$file" -o "${file%.svg}.png"
done
```

### 10. Compare target models

The adapters never download models automatically. First select and explicitly
install the desired candidates, for example:

```bash
ollama pull qwen3.5:9b
ollama pull qwen3:14b
ollama pull deepseek-r1:14b
```

Inspect the planned matrix without downloads or model calls:

```bash
uv run python -m experiments.compare_target_models --dry-run
```

Run a small Gemma 4 and Qwen 3.5 smoke test:

```bash
uv run python -m experiments.compare_target_models \
  --model gemma4 \
  --model qwen35_9b \
  --max-cases 4 \
  --repeats 1 \
  --output evaluation-results/target-model-smoke.json
```

Without `--model`, the runner compares Gemma 4 and the three recommended
Chinese models. By default, it evaluates `prompt_only` and `full_pipeline`; the
Promptbreak guard remains fixed to Gemma 4 so that only the target model changes.
The existing runner also accepts an alias for a Chinese guard classifier:

```bash
uv run python -m experiments.compare_guards \
  --target-model gemma4 \
  --promptbreak-model qwen35_9b \
  --config promptbreak_guard \
  --config full_pipeline \
  --repeats 1 \
  --output evaluation-results/qwen35-guard.json
```

### Recorded Qwen 3.5 4B run

On August 7, 2026, the full 30×5 comparison was run once with `qwen35_4b` as
both target model and Promptbreak classifier. Promptbreak achieved 13.3% ASR,
0.0% input-guard FPR, and F1 0.929; the full pipeline achieved 0.0% ASR. Two
benign inputs caused actual direct leaks from the target model, which were
caught by the output filter. Its end-to-end benign block rate is therefore
13.3%, while its input-guard FPR remains 0.0%.

- [Full Qwen guard report](evaluation-results/qwen35-4b-full-guard-comparison-2026-08-07.json)
- [Qwen threshold sweep](evaluation-results/qwen35-4b-guard-threshold-sweep-2026-08-07.json)
- [Qwen false-positive attribution](evaluation-results/qwen35-4b-false-positive-attribution-2026-08-07.json)
- [24-iteration Rainbow-lite report](evaluation-results/rainbow-lite-qwen35-4b-24-2026-08-07.json)
- [Qwen SVG gallery](evaluation-results/visualizations/qwen35-4b-2026-08-07/index.html)

This is a complete model/configuration pass, but its single repeat does not
replace the still-pending final 30×5×3 evaluation.

### Results dashboard

The [results dashboard](dashboard/index.html) summarizes the canonical Gemma,
Qwen 4B, and Qwen 27B reports, together with threshold, attribution,
Rainbow-lite, and fine-tuning diagnostics. The web application serves it at `/dashboard/`; on every
load, the page fetches a compact, hash-linked data view from the versioned JSON
reports through `/api/results`.

An API cost estimate separates input and output tokens and evaluates them
against dated pricing profiles. It is counterfactual: all measured runs were
local Ollama runs with no API cost. Because there is no direct Alibaba endpoint
for Qwen 3.5 4B, the Qwen 3.5 Flash profile is used as an explicitly labeled
proxy.

```bash
uv run python -m promptbreak
```

The web application and dashboard are then available at
`http://127.0.0.1:8000/` and `http://127.0.0.1:8000/dashboard/`. An optional
static `dashboard/data.js` snapshot can still be generated with
`uv run python -m promptbreak.dashboard`; the web application does not require it.

### Progress bars and ETA

The command modules in `experiments/` use `tqdm` for progress reporting.

- The guard comparison shows overall progress, the current configuration,
  repeat, and case ID.
- Rainbow-lite counts mutation and subsequent evaluation as separate phases so
  that the ETA does not mistake two model calls for one step.
- The ETA stabilizes after the first model calls.
- When switching between Gemma, Llama Guard, and ShieldGemma, the estimate may
  jump temporarily because load time and throughput differ.
- Progress output is written to `stderr`, leaving JSON on `stdout` parseable.

## Evaluation

In the web UI, **RUN 10-CASE EVALUATION** executes the fixed test set for the
currently active mode. For a direct comparison of both methods:

```bash
uv run python -m experiments.evaluate \
  --model gemma4:latest \
  --level 1 \
  --output evaluation-results/gemma3-4b.json
```

The evaluation records:

- **Attack Success Rate (ASR):** the share of attacks for which the secret is
  actually delivered to the client; lower is better.
- **End-to-end benign block rate:** the share of benign requests blocked by any
  layer, including intercepted target-model leaks.
- **Input-guard FPR:** the share of benign requests incorrectly blocked by the
  input guard; lower is better.
- **Accuracy:** successful attack defenses plus allowed benign requests.
- **Latency:** end-to-end runtime per case. Guarded mode usually requires an
  additional model call.

### Guard comparison

The versioned dataset
[`data/guard-evaluation.json`](data/guard-evaluation.json) contains 15 attacks
and 15 benign contrast cases with attack-like trigger words. The contrast
method is inspired by XSTest; the cases themselves are tailored to prompt
injection and Promptbreak's three levels.

Install the small local guard models once through Ollama:

```bash
ollama pull llama-guard3:1b
ollama pull shieldgemma:2b
```

A single run then compares five configurations. Three repeats produce 450
individual measurements:

```bash
uv run python -m experiments.compare_guards \
  --target-model gemma4:latest \
  --repeats 3 \
  --output evaluation-results/guard-comparison.json
```

Validate the matrix without model calls before a long run:

```bash
uv run python -m experiments.compare_guards --dry-run
```

In addition to ASR, FPR, precision, recall, and F1, the report stores:

- p50 and p95 wall-clock latency
- mean latency separated by guard refusal, deterministic legacy path, and real
  target-model path
- guard, target/application, and output-filter time
- model load time
- model calls per case
- input and output tokens
- optional hypothetical API cost when explicit token prices are supplied

Local API cost is zero. Model calls, tokens, and runtime serve as reproducible
computational-cost proxies. Llama Guard and ShieldGemma are deliberately used
out of the box: both are general content-safety guards, not classifiers trained
specifically for prompt injection.

### Evaluating the fine-tuned guard

The fine-tuned Llama classifier should be added as a separate sixth guard, not
silently substituted for the current Promptbreak guard. Evaluate it first as a
standalone classifier and then as the learned input component of the full
pipeline. Compare it with the current Promptbreak guard, Llama Guard 3,
ShieldGemma, and the official PIGuard checkpoint on identical, paired inputs.

Promptbreak Evaluation v1.1 measures application-specific attack recall and
end-to-end secret exfiltration, but its 15 benign cases are too small to support
a strong overdefense claim. A final evaluation should therefore also use the
complete, untouched 339-case NotInject benchmark. Threshold selection must use
a separate validation set, with the final test sets evaluated only once. Report
attack recall, input-guard FPR, overdefense FPR, precision, F1, balanced
accuracy, ASR, end-to-end benign blocking, latency, memory, and model calls.

Before training or evaluation, remove empty examples, resolve conflicting
labels, and group exact and near duplicates so that related prompts cannot cross
split boundaries. Run at least three training seeds and report paired confidence
intervals. The detailed protocol and acceptance criterion are documented in
[`FINE_TUNING.md`](FINE_TUNING.md).

### Rainbow-lite

`experiments/rainbow_lite.py` adopts the quality-diversity archive idea from Rainbow
Teaming, while remaining intentionally small enough for a seminar project. The
archive dimensions are attack family and transformation; the objective judge
is deterministic secret exfiltration.

```bash
uv run python -m experiments.rainbow_lite \
  --target-model gemma4:latest \
  --attacker-model qwen35_4b \
  --configuration full_pipeline \
  --iterations 24 \
  --output evaluation-results/rainbow-lite-qwen35-4b-24.json
```

The report includes archive coverage, defense progress, successful cells,
static-seed ASR, adaptive-candidate ASR, and Success@k. This is a methodically
motivated adaptation, not a reproduction of the compute-intensive original
study.

## Architecture

```text
Baseline
user input ───────────────→ target LLM + system prompt ──────→ response

Guarded
user input → rules + LLM classifier → target LLM + hardening → leak filter → response
                   │ blocked                                  │ redacted
                   └──────────────── safe refusal ────────────┘
```

The backend uses Python's small `ThreadingHTTPServer`. It serves static assets
and communicates with Ollama's local `/api/chat` endpoint. Secrets are never
sent to the browser. Session metrics exist only in memory and disappear when
the server restarts.

Intentionally vulnerable baseline paths are triggered deterministically in the
backend. This ensures that a valid solution does not depend on whether a modern
model happens to refuse the unsafe instruction. All other responses are still
generated by Ollama.

Level 3 additionally contains a reproducible attack against the guarded
pipeline. A stateless legacy allowlist trusts a three-stage recovery sequence.
The final value is emitted in a NOVA-64 wrapper (Base64): the simple plaintext
output filter misses it, but a separately implemented evaluator decodes it and
correctly counts it as exfiltration. The defense mechanism and measurement
instrument are therefore deliberately not identical.

## Research material

The submission report is available in [`report/`](report/); its BibTeX entries
are stored in [`references.bib`](references.bib).

### Defense Builder

The UI supports ablation of individual security components:

1. Heuristic Scanner
2. LLM Input Guard
3. Prompt Hardening
4. Direct Leak Filter
5. Encoding Detector
6. Context-Aware Guard

The `Prompt only`, `Input guard`, `Output filter`, `Standard`, and `Full
pipeline` presets select fixed configurations. Manual changes create a custom
configuration that immediately applies to chat and Auto Red-Team.

### Auto Red-Team Agent

The agent begins with reproducible seeds from the playbook. If the defense
holds, the selected local Ollama model analyzes the latest results and produces
a new strategy and attack prompt as structured output. A run may contain one to
five rounds and stops after a breach.

### Benchmark Heatmap

**BUILD HEATMAP** runs four attack types and one benign control request against
four defense configurations:

- Authority Claiming
- Format Smuggling
- Multi-Turn Context Poisoning
- Encoding Exfiltration

The heatmap shows attack success rate for each cell. Aggregate ASR,
false-positive rate, and mean end-to-end latency appear below it. Because the
benchmark performs real local model calls, it may take several minutes.

## Project structure

```text
project/
├── promptbreak/         # web application package
│   ├── __main__.py       # `python -m promptbreak` entry point
│   ├── main.py           # server, Ollama client, and defense pipelines
│   ├── dashboard.py      # dashboard data builder
│   ├── finetuned_guard.py # lazy PyTorch/PEFT guard inference
│   └── model_adapters.py # Ollama model aliases and request options
├── experiments/         # reproducible benchmark and analysis commands
│   ├── compare_guards.py
│   ├── compare_target_models.py
│   ├── diagnose_false_positives.py
│   ├── evaluate.py
│   ├── rainbow_lite.py
│   ├── repair_guard_report.py
│   ├── sweep_guard_thresholds.py
│   ├── visualize_results.py
│   ├── visualize_report_results.py
│   └── visualize_training.py
├── finetuning/
│   ├── overfiltering.ipynb  # experimental PIGuard-inspired Llama QLoRA training
│   └── training_log_history.json
├── FINE_TUNING.md       # provenance, limitations, and evaluation protocol
├── evaluation-results/  # versioned JSON reports and SVG analyses
├── report/              # ACL-style Typst report and compiled PDF
├── pitch/               # Typst source, graphics, and compiled pitch PDF
├── data/
│   ├── guard-evaluation.json
│   └── finetuning/
│       └── train.json   # source-tagged corpus stored with Git LFS
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── tests/               # 61 model-free unit tests
└── pyproject.toml
```

## Tests

The unit tests do not require a model:

```bash
uv run python -m unittest discover -s tests -v
```

## AI use disclosure

OpenAI Codex was used as a development assistant for language editing and
translation, repository refactoring, drafting code and tests, and producing visualization drafts. All suggested text and code
was reviewed and revised by the project authors, and reported values were
checked against the versioned JSON results and training logs.

Codex was not
treated as an empirical source or evaluation judge; the authors retain
responsibility for the design, interpretation, and final project.

This use is
separate from the local language models evaluated as part of Promptbreak.

## Limitations and safety

This project is an isolated simulation. It has no tools and does not access
files, accounts, or real credentials. An LLM guard cannot guarantee security;
the purpose of the comparison is to measure remaining attacks and false
positives. Secrets in `promptbreak/main.py` are game values, not real credentials.
