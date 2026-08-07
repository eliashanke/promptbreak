# Methods

## Research question

> How do prompt-injection-specific guardrails, general-purpose safety models,
> and layered defenses differ in application security, benign utility, latency,
> and computational cost?

The study treats prompt injection as an application-security problem rather
than only a content-safety problem. The attacker succeeds only if a protected
application secret is delivered to the client. A refusal or a guard label alone
is therefore not the end-to-end outcome.

## System under test

Promptbreak is a fully local prompt-injection laboratory built around three
intentionally vulnerable application levels:

1. a legacy QA/configuration path,
2. an unsafe structured export path,
3. a stateful recovery workflow with an encoded exfiltration path.

The vulnerable workflows are implemented deterministically in application code.
This prevents modern models from making the benchmark unwinnable by refusing
even when the application is intentionally configured to leak. All other
responses are generated through a local Ollama model.

The application uses synthetic secrets and has no tools, external side effects,
real credentials, or cloud API calls.

## Compared configurations

| Configuration     | Input protection                                  | Target/output protection                                    | Purpose                                |
| ----------------- | ------------------------------------------------- | ----------------------------------------------------------- | -------------------------------------- |
| Prompt only       | None                                              | System prompt only                                          | Unprotected baseline                   |
| Promptbreak Guard | Regex heuristics + task-specific Gemma classifier | Prompt hardening; no context or output layers               | Prompt-injection-specific input guard  |
| Llama Guard 3     | `llama-guard3:1b`                                 | No additional output layers                                 | General-purpose safety baseline        |
| ShieldGemma       | `shieldgemma:2b`                                  | No additional output layers                                 | General-purpose policy-safety baseline |
| Full Pipeline     | Promptbreak input guard + context guard           | Prompt hardening + direct output filter + encoding detector | Layered application defense            |

The target model and the Promptbreak LLM classifier were both
`gemma4:latest`. Llama Guard 3 and ShieldGemma were used out of the box and were
not fine-tuned for prompt-injection detection.

## Evaluation set

The versioned dataset `data/guard-evaluation.json` contains 30 cases:

- 15 attacks:
  - 5 authority-claiming attacks,
  - 5 format-smuggling attacks,
  - 3 multi-turn attacks,
  - 2 encoding/exfiltration attacks;
- 15 benign contrast cases:
  - 3 password-related requests,
  - 3 system-prompt-related requests,
  - 3 encoding-related requests,
  - 3 debugging-related requests,
  - 3 roleplay-related requests.

The benign cases are project-specific contrast cases inspired by the
methodology of XSTest [@rottger2024xstest] and by the overdefense motivation of
PIGuard/NotInject [@li2025piguard]. They contain attack-associated terms in
clearly benign contexts. They are not presented as an unchanged copy of
NotInject.

The attacks are either native Promptbreak cases or documented adaptations. The
dataset stores a source label for every case (`promptbreak`, `adapted`, or
`xstest-inspired`).

## Experimental protocol

The complete static comparison used:

- 30 cases,
- 5 configurations,
- 3 repetitions,
- 450 case-configuration observations in total.

The same cases, target model, secrets, and local hardware were used for every
configuration. The configurations were executed sequentially in the following
order:

1. Prompt only,
2. Promptbreak Guard,
3. Llama Guard 3,
4. ShieldGemma,
5. Full Pipeline.

The three repetitions produced identical ASR and FPR values for every
configuration. The full run produced no guard or parsing errors.

## Metrics

### End-to-end security

Attack Success Rate:

```text
ASR = successful secret exfiltrations / attack cases
```

Lower ASR is better. Exfiltration is judged deterministically after normalizing
direct strings and checking reversible forms including reversed text, ROT13,
hex, Base64, decimal bytes, binary bytes, and Unicode code points. The deployed
encoding filter intentionally covers only the first group; otherwise the filter
and objective judge would be identical and a measured bypass would be impossible.

### Benign utility

End-to-end benign block rate:

```text
benign block rate = benign cases blocked by any layer / benign cases
```

The report additionally computes input-guard FPR from `trace.input_guard` only.
This distinction matters when a benign request passes the classifier but the
target model leaks a secret that the output filter correctly redacts. Lower
values are better, but a caught output leak must not be described as an input-
classifier false positive.

### Guard/defense classification

Attack cases are treated as positive examples and benign cases as negative
examples:

- true positive: attack blocked,
- false negative: attack not blocked,
- false positive: benign case blocked,
- true negative: benign case allowed.

Precision, recall, and F1 are computed from these counts. For the Full Pipeline,
`blocked` represents the final defense action and may include an output-layer
block, not only an input-classifier decision. New summaries therefore report
the end-to-end confusion matrix, an input-guard confusion matrix, and output-
leak catches separately.

### Latency and compute

The report records:

- mean end-to-end latency,
- warm p50 and p95 latency using repetitions 2 and 3,
- model-load duration,
- model calls,
- prompt and completion tokens,
- tokens per case.

New reports also separate guard time, target/application time, and output-filter
time for guard refusals, deterministic legacy paths, and genuine target-model
paths. Historical JSON artifacts predate this instrumentation.

Local Ollama API cost is EUR 0. Model calls, tokens, and wall-clock time are
reported as computational-cost proxies.

Latency values are path-dependent. Deterministic attack paths may take nearly
zero milliseconds, guard refusals can avoid the target model, and allowed
benign cases invoke the large target model. Latency must therefore be
interpreted together with blocking behavior.

## Adaptive evaluation

Rainbow-Lite is a seminar-scale adaptation of Rainbow Teaming
[@samvelyan2024rainbow]. It uses:

- attack family as one archive dimension,
- transformation type as the second dimension,
- deterministic secret exfiltration as the objective judge,
- one elite prompt per archive cell.

The recorded historical run used four direct seeds and eight adaptive mutations
against the Full Pipeline. The revised protocol evaluates 24 adaptive
candidates, revisits every non-direct cell twice, selects the strongest
same-family elite as parent, and rewards intermediate defense progress before
lexical novelty. Mutations that erase the attack objective by substituting a
placeholder are rejected and regenerated up to three times. This remains a
small quality-diversity experiment, not a
reproduction of the original distributed MAP-Elites study.

## False-positive attribution

A separate benign-only diagnostic compared:

1. regex heuristics alone,
2. the Gemma classifier with heuristics disabled,
3. their logical OR, which matches the Promptbreak input-guard decision.

Each of the 15 benign cases was assigned to one of four attribution classes:
`heuristics_only`, `llm_only`, `both`, or `neither`.

Context and output layers are intentionally not re-run in this diagnostic. It
attributes input-guard false positives only. End-to-end benign blocks caused by
context rules or by genuine model leaks caught at the output must be reported
separately rather than counted as classifier false positives.

## Post-hoc guard-tuning protocol

The false-positive analysis motivated an engineering iteration on the
Promptbreak input guard. The revised heuristic requires joint evidence of a
protected target and an extraction, override, structured-export, or
recovery-export action. The Gemma classifier prompt explicitly labels benign
meta-discussion, translation, password guidance, encoding explanations,
debugging, and non-extractive roleplay as safe.

The revised result trace records:

- the independent heuristic decision and matched rule names,
- the raw LLM malicious label, confidence, category, and reason,
- the confidence threshold and thresholded LLM block,
- the combined decision and the layers responsible for a block,
- a separate Context Guard decision when it short-circuits the other input
  layers.

A threshold sweep classified the 30 cases once at temperature 0 and recomputed
decisions for thresholds 0.50, 0.55, 0.70, 0.80, 0.90, 0.95, and 0.99. A
targeted end-to-end validation then reran Promptbreak Guard and Full Pipeline
for one complete repetition at the retained default threshold of 0.55.

This tuning protocol used the original evaluation set as a development set.
Its result is therefore reported separately from the initial three-repetition
comparison.

## Implementation and progress reporting

The runners are implemented in:

- `compare_guards.py`,
- `rainbow_lite.py`,
- `diagnose_false_positives.py`.
- `sweep_guard_thresholds.py`.

All long-running command-line evaluations use `tqdm`. Progress output is sent
to `stderr`, while machine-readable JSON remains on `stdout`.
