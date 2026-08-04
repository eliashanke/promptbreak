# Reproducibility

## Environment

Required:

- Python 3.9 or newer,
- `uv`,
  - Get it using `brew install uv`
- Ollama,
- enough local memory for `gemma4:latest`,
- the models listed below.

Install the Python environment:

```bash
cd project
uv sync
```

Install models:

```bash
ollama pull gemma4:latest
ollama pull llama-guard3:1b
ollama pull shieldgemma:2b
ollama list
```

Models used in the recorded run:

| Role                   | Model             |
| ---------------------- | ----------------- |
| Target model           | `gemma4:latest`   |
| Promptbreak classifier | `gemma4:latest`   |
| General guard 1        | `llama-guard3:1b` |
| General guard 2        | `shieldgemma:2b`  |
| Rainbow-Lite attacker  | `gemma4:latest`   |

Recorded hardware and runtime environment:

| Component        | Recorded value                          |
| ---------------- | --------------------------------------- |
| Machine          | MacBook Pro, model identifier `Mac16,8` |
| Chip             | Apple M4 Pro                            |
| CPU cores        | 12 total: 8 performance, 4 efficiency   |
| Unified memory   | 24 GB                                   |
| Architecture     | ARM64                                   |
| Operating system | macOS 26.5.2, build `25F84`             |
| Ollama client    | 0.23.0                                  |

Ollama model identifiers observed before the run:

| Model             | Identifier     |
| ----------------- | -------------- |
| `gemma4:latest`   | `c6eb396dbd59` |
| `llama-guard3:1b` | `494147e06bf9` |
| `shieldgemma:2b`  | `5aad5044d142` |

## Tests

```bash
uv run python -m unittest discover -s tests -v
```

Recorded status after guard tuning: 33/33 tests passed.

## Validate the static matrix

```bash
uv run python compare_guards.py \
  --target-model gemma4:latest \
  --repeats 3 \
  --dry-run
```

Expected result:

```json
{
  "cases": 30,
  "attacks": 15,
  "benign": 15,
  "repeats": 3,
  "planned_runs": 450
}
```

## Run the complete static comparison

```bash
uv run python compare_guards.py \
  --target-model gemma4:latest \
  --promptbreak-model gemma4:latest \
  --llama-guard-model llama-guard3:1b \
  --shieldgemma-model shieldgemma:2b \
  --repeats 3 \
  --output evaluation-results/full-guard-comparison.json
```

Observed runtime on the seminar machine: 4,011,564 ms, or 66.86 minutes.

The runner displays:

- overall case progress,
- current configuration,
- current repetition,
- current case ID,
- elapsed time and ETA.

The ETA can change after model transitions because model size, cache state, and
the probability of invoking the target model differ by configuration.

## Run false-positive attribution

```bash
uv run python diagnose_false_positives.py \
  --model gemma4:latest \
  --output evaluation-results/false-positive-attribution.json
```

Observed runtime: approximately 92 seconds for 15 benign classifier calls.
After the first few cases, throughput stabilized at approximately 6 seconds per
case.

## Run the confidence-threshold sweep

```bash
uv run python sweep_guard_thresholds.py \
  --model gemma4:latest \
  --output evaluation-results/guard-threshold-sweep.json
```

The runner makes one deterministic Gemma call per case, then evaluates all
thresholds offline against the same raw labels and confidence values. The
default thresholds are 0.50, 0.55, 0.70, 0.80, 0.90, 0.95, and 0.99.

## Validate the tuned guard end to end

```bash
uv run python compare_guards.py \
  --target-model gemma4:latest \
  --promptbreak-model gemma4:latest \
  --promptbreak-threshold 0.55 \
  --config promptbreak_guard \
  --config full_pipeline \
  --repeats 1 \
  --output evaluation-results/tuned-guard-validation.json
```

Recorded runtime: 926,079 ms, or 15.43 minutes, for 60 case-configuration
observations.

## Run Rainbow-Lite

```bash
uv run python rainbow_lite.py \
  --target-model gemma4:latest \
  --attacker-model gemma4:latest \
  --configuration full_pipeline \
  --iterations 8 \
  --output evaluation-results/rainbow-lite.json
```

Observed runtime: 156,913 ms, or 2.62 minutes.

Rainbow-Lite counts seed evaluation, mutation, and candidate evaluation as
separate progress stages. Eight iterations produce:

```text
4 seed stages + (8 × 2 adaptive stages) = 20 progress stages
```

## Generate visualizations

The current visualization script reads the datestamped canonical reports:

```bash
uv run python visualize_results.py
```

It writes SVGs and an HTML gallery to:

```text
evaluation-results/visualizations/
```

Optional PNG rendering:

```bash
for file in evaluation-results/visualizations/*.svg; do
  rsvg-convert -w 1600 "$file" -o "${file%.svg}.png"
done
```

## Canonical artifacts and checksums

### Static comparison

Path:

```text
evaluation-results/full-guard-comparison-2026-07-30.json
```

SHA-256:

```text
d2275be8f9f2e5a8dd9aee8f0bd335b3f36691f7ca68a517515a909c0bddde40
```

### Rainbow-Lite

Path:

```text
evaluation-results/rainbow-lite-full-pipeline-2026-07-30.json
```

SHA-256:

```text
948092bebb059aca6abb97f78cda54bb4746b9aa102cf753a937f27bb27dc8c9
```

### False-positive attribution

Path:

```text
evaluation-results/false-positive-attribution-2026-07-30.json
```

SHA-256:

```text
53cd651636967f3a94791209e37cd73f213c8c478eb29a9fe54c7d9270e41943
```

### Guard threshold sweep

Path:

```text
evaluation-results/guard-threshold-sweep-2026-07-30.json
```

SHA-256:

```text
459c1ec5fc1da9ee01e0c4d76a3e856aad9d062192849fada9ec629f67198623
```

### Tuned guard validation

Path:

```text
evaluation-results/tuned-guard-validation-2026-07-30.json
```

SHA-256:

```text
e5175dc3c5f76a8fadf98401707c3d716010d4f5422023df29a8012e4a1627a9
```

## Progress output and JSON output

All long-running runners use `tqdm`. Progress is written to `stderr`, while JSON
is printed to `stdout`. This permits redirection without mixing the progress bar
into the result:

```bash
uv run python compare_guards.py --dry-run \
  > matrix.json \
  2> progress.log
```

When `--output` is supplied, the canonical report is written directly to the
specified file.
