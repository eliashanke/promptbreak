# Promptbreak Report Notes

Status: 30 July 2026

This directory contains the English report material for Promptbreak. The files
separate measured results from interpretation and future work. Reported numbers
are traceable to versioned JSON artifacts.

## Files

- [`METHODS.md`](METHODS.md): research question, system, dataset, configurations,
  metrics, and experimental protocol.
- [`EVALUATION_SUITE.md`](EVALUATION_SUITE.md): intentionally vulnerable game
  contracts, all attack families, benign contrast cases, and objective judging.
- [`RESULTS.md`](RESULTS.md): complete static comparison, category breakdown,
  latency, compute, and Rainbow-Lite results.
- [`FALSE_POSITIVE_ANALYSIS.md`](FALSE_POSITIVE_ANALYSIS.md): causal attribution
  of the Full Pipeline's false positives.
- [`GUARD_TUNING.md`](GUARD_TUNING.md): refined rules, separated traces,
  threshold sweep, regression tests, and targeted end-to-end validation.
- [`DISCUSSION_AND_LIMITATIONS.md`](DISCUSSION_AND_LIMITATIONS.md): interpretation,
  validity threats, and defensible claims.
- [`REPRODUCIBILITY.md`](REPRODUCIBILITY.md): environment, commands, artifacts,
  progress bars, and expected runtimes.
- [`REPORT_OUTLINE.md`](REPORT_OUTLINE.md): proposed report structure, figures,
  and central claims.

## Canonical result artifacts

- `evaluation-results/full-guard-comparison-2026-07-30.json`
- `evaluation-results/rainbow-lite-full-pipeline-2026-07-30.json`
- `evaluation-results/false-positive-attribution-2026-07-30.json`
- `evaluation-results/visualizations/index.html`

## Headline results

In the initial three-repetition comparison, the Full Pipeline prevented every
tested secret exfiltration but blocked 14 of 15 benign contrast cases. A
follow-up attribution experiment showed that context-insensitive keyword
heuristics were responsible for 13 false positives on their own and
contributed to the remaining shared false positive.

After replacing isolated keyword blocks with multi-signal rules and clarifying
the Gemma classifier prompt, a targeted one-repetition validation reduced FPR
to 0% for both Promptbreak Guard and Full Pipeline. Their ASR values remained
13.3% and 0%, respectively. Because the same benchmark informed the repair,
this is a development-set result pending a final repeated run and unseen
holdout evaluation.

## Terminology

The report should distinguish:

1. **Detection:** whether a defense labels or blocks an attack.
2. **Application security:** whether the protected secret reaches the client.
3. **Utility:** whether a benign request is allowed.

A defense that blocks everything has low attack success, but it is not a useful
application-level solution.
