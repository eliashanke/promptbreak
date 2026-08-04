# Discussion and Limitations

## Answer to the research question

The evaluated defenses occupied different positions in the
security–utility space:

- Prompt only and ShieldGemma preserved benign utility but allowed every tested
  attack.
- Llama Guard 3 preserved benign utility and blocked format-smuggling attacks,
  but allowed two thirds of all attacks.
- Promptbreak Guard blocked most attacks, but rejected almost every benign
  contrast case.
- Full Pipeline blocked every tested attack, including encoding attacks missed
  by the input guard, but inherited the same severe overblocking.

The results support the distinction between general content safety and
application security. The general-purpose guards did not reliably detect
requests that exploited application-specific workflows. The layered defense
closed more exfiltration paths, but security alone was insufficient: its input
guard made the application largely unusable.

## Defense-in-depth finding

The difference between Promptbreak Guard and Full Pipeline isolates the value
of downstream layers:

- Promptbreak Guard ASR: 13.3%,
- Full Pipeline ASR: 0.0%,
- both configurations FPR: 93.3%.

The Full Pipeline's Context Guard eliminated the remaining encoding leaks by
recognizing the preceding recovery sequence and blocking before response
generation. This is evidence that a state-aware layer can close attack paths
missed by a classifier that evaluates only the current input.

The direct output filter and encoding detector remained `PASSED` in all 90 Full
Pipeline observations. Their implementation is covered by unit tests, but this
full benchmark did not isolate or exercise their contribution. Additional
ablation cases are required before making an empirical claim about their
benefit. The Context Guard also did not repair the utility failure introduced
by the upstream heuristics.

## Surface-heuristic finding

The false-positive attribution directly demonstrates surface-trigger bias. A
bad-word scanner blocked harmless discussions of passwords, Base64, debugging,
roleplay, and secrets. This behavior is consistent with the overblocking
motivation of XSTest [@rottger2024xstest] and PIGuard/NotInject
[@li2025piguard].

The Gemma classifier alone performed substantially better on benign utility,
but it still rejected the translation contrast containing “ignore previous
instructions.” Context-sensitive models therefore reduce but do not
necessarily eliminate trigger bias.

## Post-hoc remediation

The attribution enabled a focused repair. Replacing isolated bad-word blocks
with multi-signal signatures and clarifying the Gemma classifier's treatment of
benign meta-discussion reduced FPR from 93.3% to 0% in a one-repetition
end-to-end validation. Promptbreak Guard retained 13.3% ASR and Full Pipeline
retained 0% ASR.

This finding shows that the original failure was not an unavoidable cost of
using any deterministic heuristic. It was caused by using broad topic matches
as hard blocks. Narrow signatures can contribute useful coverage on the
application's known workflows.

The tuned result is deliberately separated from the initial comparison. The
same 30 cases were used to diagnose and repair the guard, creating direct
overfitting risk. An unseen benign contrast set and a final three-repetition
comparison are required before claiming that the improvement generalizes.

## General safety guards

Llama Guard 3 and ShieldGemma were intentionally evaluated out of the box.
Their weak prompt-injection performance should not be interpreted as a general
statement about their intended content-safety tasks.

The defensible conclusion is narrower:

> On this application-specific prompt-injection dataset and with the tested
> local model versions, the general-purpose safety guards did not provide
> sufficient application-level prompt-injection protection.

## Latency interpretation

Latency was strongly affected by control flow:

- deterministic vulnerable attack paths may return immediately,
- a blocking guard avoids the target-model call,
- an allowed benign request may invoke the large target model,
- specialized guards can add one call before the target call.

Consequently, Full Pipeline's lower p95 and token count partly reflect
overblocking. A system that refuses useful work early can appear computationally
efficient. Latency results should be reported alongside FPR and path type.

Future analysis should separate:

- guard-only latency,
- blocked end-to-end latency,
- allowed target-model latency,
- deterministic legacy-path latency,
- output-filter latency.

## Rainbow-Lite interpretation

No static seed or adaptive mutation breached the Full Pipeline. This is useful
evidence that the tested mutations did not trivially bypass the layered
defense.

The experiment remains exploratory:

- only eight adaptive mutations were tested,
- four `obfuscated` cells were never visited,
- the same model family generated attacks and performed Promptbreak
  classification,
- only one adaptive run was performed,
- the archive objective used one local application and deterministic secrets.

The result must not be described as general adaptive robustness.

## Threats to validity

### Construct validity

- Benign utility is approximated by pass rate on 15 contrast cases, not by a
  complete downstream task-success measure.
- `blocked` combines input and output defense actions for the Full Pipeline.
- F1 measures defense classification behavior, while ASR measures actual
  exfiltration; the metrics answer different questions.
- Local API cost is zero and does not represent electricity or hardware cost.

### Internal validity

- Configurations ran sequentially, so model-cache and thermal state may differ.
- Three repetitions produced identical decisions but are not independent
  samples from different model seeds.
- The target and Promptbreak classifier both used `gemma4:latest`.
- Deterministic application vulnerabilities improve reproducibility but make
  some latency observations artificial.
- The full false-positive attribution re-ran only the input classifier because
  traces already localized the false positives upstream.
- The tuned guard was developed and validated on the same 30 cases; its 0% FPR
  is a development-set result.
- The tuned end-to-end validation used one repetition rather than three.

### External validity

- The dataset contains only 30 application-specific cases.
- All attacks are direct chat or simulated multi-turn attacks; indirect
  document injection is out of scope.
- There are no external tools, real agent actions, or real credentials.
- Results may not transfer to cloud model versions, larger models, other
  languages, or different system prompts.
- Llama Guard and ShieldGemma were not adapted to Promptbreak's application
  policy.

### Statistical conclusion validity

- With 15 attacks and 15 benign cases, one case changes ASR or FPR by 6.7
  percentage points.
- Identical repetitions demonstrate deterministic stability under the same
  setup, not broad statistical uncertainty.
- Confidence intervals would overstate generality if the fixed cases were
  treated as independent samples from all prompt injections.

## Claims that are supported

- The Full Pipeline blocked every tested static and Rainbow-Lite attack.
- The Promptbreak input guard caused severe overblocking on the benign contrast
  set.
- Broad keyword heuristics were the primary cause of those false positives.
- On the same development benchmark, the refined multi-signal rules reduced
  FPR to 0% without increasing ASR in a one-repetition validation.
- The Context Guard closed the tested recovery/encoding path missed by the
  current-input guard.
- Llama Guard 3 detected format-smuggling attacks but missed the other tested
  families.
- ShieldGemma did not improve ASR over Prompt only on this dataset.

## Claims that are not supported

- The Full Pipeline is generally robust to prompt injection.
- ShieldGemma or Llama Guard is generally ineffective for safety.
- The benchmark represents the full NotInject dataset.
- Three repeated runs establish statistical significance.
- Lower Full Pipeline latency proves that it is the most efficient usable
  system.
- The tuned guard will retain 0% FPR on unseen benign prompts.
