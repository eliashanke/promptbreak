# Results

## Static comparison

Each configuration was evaluated on 30 cases for three repetitions, resulting
in 90 observations per configuration and 450 observations overall.

| Configuration     |  ASR ↓ | Attack block rate ↑ | FPR ↓ | Precision | Recall |    F1 |
| ----------------- | -----: | ------------------: | ----: | --------: | -----: | ----: |
| Prompt only       | 100.0% |                0.0% |  0.0% |     0.000 |  0.000 | 0.000 |
| Promptbreak Guard |  13.3% |               86.7% | 93.3% |     0.481 |  0.867 | 0.619 |
| Llama Guard 3     |  66.7% |               33.3% |  0.0% |     1.000 |  0.333 | 0.500 |
| ShieldGemma       | 100.0% |                0.0% |  0.0% |     0.000 |  0.000 | 0.000 |
| Full Pipeline     |   0.0% |              100.0% | 93.3% |     0.517 |  1.000 | 0.682 |

No configuration reached the desired low-ASR, low-FPR region.

### Absolute outcomes per repetition

The repetitions were identical. For one 30-case repetition:

| Configuration     | Successful attacks | Benign cases blocked |
| ----------------- | -----------------: | -------------------: |
| Prompt only       |              15/15 |                 0/15 |
| Promptbreak Guard |               2/15 |                14/15 |
| Llama Guard 3     |              10/15 |                 0/15 |
| ShieldGemma       |              15/15 |                 0/15 |
| Full Pipeline     |               0/15 |                14/15 |

The Full Pipeline achieved complete protection on the tested attacks, but only
one benign request remained usable.

## Attack-family breakdown

The table reports ASR by family. Lower values are better.

| Configuration     | Authority | Format smuggling | Multi-turn | Encoding |
| ----------------- | --------: | ---------------: | ---------: | -------: |
| Prompt only       |      100% |             100% |       100% |     100% |
| Promptbreak Guard |        0% |               0% |         0% |     100% |
| Llama Guard 3     |      100% |               0% |       100% |     100% |
| ShieldGemma       |      100% |             100% |       100% |     100% |
| Full Pipeline     |        0% |               0% |         0% |       0% |

The Promptbreak input guard detected authority, format-smuggling, and
multi-turn attacks, but missed both encoding attacks. In the Full Pipeline, the
Context Guard recognized the preceding recovery sequence and blocked both
encoding cases before response generation. Llama Guard 3 detected the
format-smuggling family but missed all tested authority, multi-turn, and
encoding attacks. ShieldGemma produced the same attack outcome as Prompt only.

The direct output filter and encoding detector reported `PASSED` for all 90 Full
Pipeline observations. They were therefore not exercised by this particular
benchmark run and cannot be credited with the observed ASR improvement.

## Benign-category breakdown

The table reports FPR by benign trigger category. Lower values are better.

| Configuration     | Debugging | Encoding | Password | Roleplay | System prompt |
| ----------------- | --------: | -------: | -------: | -------: | ------------: |
| Prompt only       |        0% |       0% |       0% |       0% |            0% |
| Promptbreak Guard |      100% |     100% |     100% |     100% |           67% |
| Llama Guard 3     |        0% |       0% |       0% |       0% |            0% |
| ShieldGemma       |        0% |       0% |       0% |       0% |            0% |
| Full Pipeline     |      100% |     100% |     100% |     100% |           67% |

The overblocking was systematic rather than limited to a single category.
Promptbreak Guard and Full Pipeline blocked every benign debugging, encoding,
password, and roleplay case, plus two of three benign system-prompt cases.

## Confusion matrices

Counts are aggregated across three repetitions.

| Configuration     |   TP |   FP |   TN |   FN |
| ----------------- | ---: | ---: | ---: | ---: |
| Prompt only       |    0 |    0 |   45 |   45 |
| Promptbreak Guard |   39 |   42 |    3 |    6 |
| Llama Guard 3     |   15 |    0 |   45 |   30 |
| ShieldGemma       |    0 |    0 |   45 |   45 |
| Full Pipeline     |   45 |   42 |    3 |    0 |

## Latency and computational cost

| Configuration     | Warm p50 | Warm p95 | Model calls | Calls/case | Tokens/case |
| ----------------- | -------: | -------: | ----------: | ---------: | ----------: |
| Prompt only       |  0.000 s | 23.485 s |          45 |      0.500 |       511.8 |
| Promptbreak Guard | 11.585 s | 21.434 s |          87 |      0.967 |       228.0 |
| Llama Guard 3     |  0.126 s | 21.379 s |         135 |      1.500 |       728.0 |
| ShieldGemma       |  0.424 s | 23.298 s |         135 |      1.500 |       867.4 |
| Full Pipeline     |  6.268 s | 10.228 s |          78 |      0.867 |       202.5 |

Across all configurations, the static run used:

- 480 actual model calls,
- 103,524 prompt tokens,
- 124,875 completion tokens,
- 228,399 tokens in total,
- 66.86 minutes of wall-clock runtime,
- EUR 0 local API cost.

The Full Pipeline's lower p95 and token count should not be interpreted as an
unconditional efficiency advantage. It blocked 93.3% of benign cases before
many could reach the target model. Its apparent efficiency is therefore partly
a consequence of low utility.

ShieldGemma had the largest token cost per case while providing no measurable
security improvement over Prompt only on this dataset.

## Rainbow-Lite

The Full Pipeline was evaluated with four static seeds and eight adaptive
mutations.

| Metric                   |  Result |
| ------------------------ | ------: |
| Static seed ASR          |    0.0% |
| Adaptive candidate ASR   |    0.0% |
| Adaptive Success@k       |    None |
| Successful archive cells |       0 |
| Occupied archive cells   |   12/16 |
| Archive coverage         |     75% |
| Runtime                  | 156.9 s |

All tested seeds and mutations were blocked. However, the four `obfuscated`
cells were not reached within eight iterations. The result supports only the
claim that none of the tested adaptive candidates succeeded; it does not
establish general adaptive robustness.

## False-positive attribution

The separate 15-case diagnostic produced:

| Attribution     | Cases |
| --------------- | ----: |
| Heuristics only |    13 |
| LLM only        |     0 |
| Both            |     1 |
| Neither         |     1 |

The heuristics blocked 14/15 benign cases, while the Gemma classifier without
heuristics blocked only 1/15. No diagnostic calls failed.

## Post-hoc guard tuning

After the causal analysis, the heuristic scanner was changed from isolated
keyword blocks to multi-signal signatures, and the Gemma classifier prompt was
expanded with explicit benign contrast instructions.

A one-repetition, 30-case end-to-end validation produced:

| Configuration | ASR before | ASR tuned | FPR before | FPR tuned |
| --- | ---: | ---: | ---: | ---: |
| Promptbreak Guard | 13.3% | 13.3% | 93.3% | 0.0% |
| Full Pipeline | 0.0% | 0.0% | 93.3% | 0.0% |

All 15 benign requests passed both tuned configurations, and the Full Pipeline
still blocked all 15 attacks. No guard or parsing errors occurred.

This is a targeted post-hoc validation, not a replacement for the initial
three-repetition comparison. The revised rules were designed using the same
contrast cases, so the result may overestimate performance on unseen prompts.
The complete tuning analysis and threshold sweep are reported in
[`GUARD_TUNING.md`](GUARD_TUNING.md).

## Figures

Generated figures are available under `evaluation-results/visualizations/`:

- `security-utility.svg`,
- `category-heatmaps.svg`,
- `latency-compute.svg`,
- `rainbow-lite.svg`.

The HTML gallery is `evaluation-results/visualizations/index.html`.
