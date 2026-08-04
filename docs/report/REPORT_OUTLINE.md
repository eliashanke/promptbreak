# Proposed Report Outline

## Working title

**Promptbreak: Measuring the Security–Utility Trade-off of Local
Prompt-Injection Defenses**

## Abstract

Recommended structure:

1. Prompt injection threatens application goals, not only content safety.
2. Promptbreak compares five local defense configurations on a fixed 30-case
   attack/benign contrast set.
3. The experiment reports end-to-end attack success, false positives, latency,
   and compute proxies across three repetitions.
4. The Full Pipeline stopped all tested attacks but blocked 93.3% of benign
   cases.
5. A layer attribution showed that broad keyword heuristics caused nearly all
   false positives.
6. A post-hoc refinement reduced FPR to 0% without increasing ASR in a targeted
   one-repetition validation.
7. Because the same cases informed the refinement, a repeated run and unseen
   holdout remain necessary.

Do not claim general robustness or statistical significance.

## 1. Introduction

Suggested points:

- A model may be generally safe while the surrounding application remains
  vulnerable.
- Input classification alone does not measure whether a protected secret
  reaches the client.
- A guard that rejects every suspicious word is secure in a trivial sense but
  unusable.
- The project asks how prompt-specific, general-purpose, and layered defenses
  trade security against benign utility and compute.

Contribution statement:

> We present a small, fully local and traceable prompt-injection laboratory that
> evaluates five defense configurations with both attack and benign contrast
> cases, separates guard detection from end-to-end exfiltration, and attributes
> overblocking to individual defense components.

## 2. Related Work

Recommended organization:

### Prompt-injection benchmarks

- Formalization and direct attacks: `liu2023formalizing`
- Indirect injection as out-of-scope extension: `yi2023bipia`

### Overdefense and contrast sets

- XSTest: `rottger2024xstest`
- PIGuard/NotInject: `li2025piguard`

### Structured and layered defenses

- StruQ: `chen2024struq`

### Adaptive red teaming

- Rainbow Teaming: `samvelyan2024rainbow`

The report should state that Promptbreak's 15 benign cases are
XSTest-/NotInject-inspired project cases, not the full original datasets.

## 3. System

Include:

- the three vulnerable levels,
- deterministic application paths,
- objective secret judge,
- six independently selectable defense layers,
- local Ollama execution,
- absence of real credentials and external side effects.

Recommended figure:

- the defense-pipeline diagram from `pitch/assets/defense-pipeline.svg`.

## 4. Experimental Setup

Subsections:

1. research question,
2. five configurations,
3. 30-case dataset,
4. three-repetition protocol,
5. metrics,
6. local models,
7. Rainbow-Lite setup,
8. false-positive attribution.

Source material:

- `METHODS.md`.
- `EVALUATION_SUITE.md`.

## 5. Results

Recommended sequence:

### 5.1 Security–utility trade-off

Use:

- `evaluation-results/visualizations/security-utility.svg`.

Main observation:

> No tested configuration achieved both low ASR and low FPR.

### 5.2 Attack-family behavior

Use the upper half of:

- `evaluation-results/visualizations/category-heatmaps.svg`.

Main observation:

> The Promptbreak input guard missed encoding, Llama Guard detected
> format-smuggling only, and ShieldGemma did not change application-level ASR.

### 5.3 Benign utility

Use the lower half of the same heatmap.

Main observation:

> Promptbreak overblocking was systematic across benign categories.

### 5.4 Latency and compute

Use:

- `evaluation-results/visualizations/latency-compute.svg`.

State explicitly that early refusal reduces apparent compute.

### 5.5 Adaptive evaluation

Use:

- `evaluation-results/visualizations/rainbow-lite.svg`.

State that the four obfuscated cells were not tested within `k = 8`.

## 6. Error Analysis

Central result:

> Thirteen benign cases were blocked only by keyword heuristics, one by both
> heuristics and Gemma, and none by Gemma alone.

Use:

- `FALSE_POSITIVE_ANALYSIS.md`,
- `evaluation-results/false-positive-attribution-2026-07-30.json`.

Recommended small table:

| Attribution | Cases |
| --- | ---: |
| Heuristics only | 13 |
| LLM only | 0 |
| Both | 1 |
| Neither | 1 |

Discuss the translation case containing “ignore previous instructions” and the
hyphenated `System-Prompt` true negative.

## 7. Guard refinement

Report the engineering iteration separately from the initial comparison:

1. isolated topic keywords were replaced by multi-signal signatures,
2. the Gemma prompt explicitly distinguishes benign meta-discussion,
3. heuristic and LLM decisions are preserved separately in the trace,
4. a threshold sweep showed that confidence values had little ranking value,
5. the targeted validation retained ASR while reducing FPR to 0%.

Use:

- `GUARD_TUNING.md`,
- `evaluation-results/guard-threshold-sweep-2026-07-30.json`,
- `evaluation-results/tuned-guard-validation-2026-07-30.json`.

Label this as a development-set result rather than an unbiased final
evaluation.

## 8. Discussion

Suggested structure:

1. content safety is not application security,
2. the Context Guard closed the tested multi-turn encoding path,
3. broad keyword hard blocks broke utility,
4. lower compute can be an artifact of refusal,
5. adaptive evidence is promising but small.
6. narrow deterministic signatures repaired the observed failure in-sample,
   but require unseen validation.

Use:

- `DISCUSSION_AND_LIMITATIONS.md`.

## 9. Limitations

Must include:

- 30 application-specific cases,
- 15 benign cases,
- no indirect document injection,
- no tools or real agent side effects,
- deterministic vulnerable paths,
- sequential local runs,
- same Gemma model for target and Promptbreak classification,
- general guards used out of the box,
- three identical repetitions are not independent evidence,
- only eight Rainbow-Lite mutations.
- the tuned guard was developed and validated on the same 30 cases,
- the tuned end-to-end validation used one repetition.

## 10. Conclusion

Copy-ready conclusion:

> The experiments show that preventing tested prompt-injection leaks is not
> sufficient for a useful defense. The Full Pipeline eliminated all observed
> exfiltrations, including encoded leaks missed by the input classifier, but its
> broad keyword heuristics rejected nearly every benign contrast request.
> Layer attribution localized the utility problem to the input heuristics,
> while the Context Guard closed the tested multi-turn encoding path without
> causing the observed benign blocks. Replacing isolated keyword blocks with
> multi-signal rules reduced FPR to 0% without increasing ASR in a targeted
> development-set validation. This repair is promising but requires a repeated
> full comparison and unseen benign cases before it can be treated as evidence
> of generalization. The output filters also require targeted ablations.

## Appendix

Include:

- exact commands from `REPRODUCIBILITY.md`,
- model versions and hardware,
- complete configuration definitions,
- dataset case IDs and source labels,
- artifact checksums,
- optional full confusion matrices.
