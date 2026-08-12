// Promptbreak seminar report.
#import "@preview/tracl:0.8.1": *
#import "@preview/pergamon:0.7.1": *
#add-bib-resource(read("../references.bib"))

#show: doc => acl(
  doc,
  anonymous: false,
  title: [Promptbreak: Evaluating Layered Defenses Against Prompt Injection in a Local Security Game],
  authors: make-authors(
    (name: "Amirreza Tarabkhah", affiliation: [Heidelberg University \ #email("@cl.uni-heidelberg.de")]),
    (name: "Zakey Sodo", affiliation: [Heidelberg University \ #email("@cl.uni-heidelberg.de")]),
    (name: "Elias Hanke", affiliation: [Heidelberg University \ #email("hanke@cl.uni-heidelberg.de")]),
  ),
)

#abstract[
  Prompt injection remains a practical obstacle to deploying language-model
  applications that combine trusted instructions with untrusted user input.
  We present *Promptbreak*, a fully local educational security game and
  evaluation laboratory for comparing prompt-injection defenses. The system
  exposes three intentionally vulnerable levels and evaluates five defense
  configurations: prompt-only protection, a task-specific input guard, Llama
  Guard 3, ShieldGemma, and a layered pipeline that adds prompt hardening,
  context checks, and deterministic output filtering. Our frozen benchmark
  contains 15 attacks and 15 benign contrast cases designed to expose both
  missed attacks and overblocking. In a complete single-pass evaluation with
  Qwen 3.5 4B, prompt-only and ShieldGemma allow all attacks, Llama Guard blocks
  one third, the Promptbreak input guard reduces attack success to 13.3%, and
  the full pipeline prevents all measured attacks. The latter blocks two benign
  requests end to end because the target model itself leaks a synthetic secret;
  its input-guard false-positive rate remains zero. A seminar-scale adaptive
  Rainbow-lite run covers all 16 archive cells without finding a bypass. These
  results support layered, application-specific defenses, while the small and
  intentionally vulnerable benchmark prevents claims of general robustness.
]

= Introduction

Large language model (LLM) applications routinely place trusted system
instructions and untrusted text in the same context. Prompt injection exploits
this shared instruction channel: an attacker supplies text that causes the
model to disregard the application's intended policy or reveal protected
information. System prompts alone are therefore not a security boundary, and
general content-safety classifiers need not recognize application-specific
instruction attacks #citep("liu2023formalizing").

Defenses face a two-sided problem. Missing an attack can expose protected state,
whereas rejecting benign requests that merely contain suspicious vocabulary
makes an application unusable. This second failure mode, often called
overdefense, motivates contrast sets such as NotInject and XSTest
#citep("li2025piguard", "rottger2024xstest"). Security evaluation should consequently
measure attack success and benign utility together, alongside the latency and
compute introduced by additional model calls.

We introduce *Promptbreak*, a local prompt-injection escape room coupled to a
reproducible evaluation harness. Its purpose is both pedagogical and empirical:
users can inspect each defense decision while the same implementation is tested
on a versioned benchmark. Our research question is:

#quote[
  How do task-specific prompt-injection guardrails, general safety models, and
  layered defense pipelines differ in attack success rate, false-positive rate,
  latency, and computational cost?
]

Our contributions are: (1) an interactive, fully local testbed with three
reproducible vulnerability classes; (2) a frozen 30-case benchmark pairing
attacks with benign, trigger-rich contrasts; (3) a common evaluation of five
defense configurations with path-level latency and compute telemetry; and (4) a
small quality-diversity experiment for adaptive attacks.

= Related Work

Liu et al. formalize prompt-injection attacks and compare attacks, defenses,
models, and tasks, establishing the terminology used in this work
#citep("liu2023formalizing"). BIPIA extends evaluation to indirect injections embedded
in documents and other external content #citep("yi2023bipia"). Promptbreak currently
focuses on direct chat input and multi-turn state, so indirect injection remains
outside our experimental scope.

Several defenses explicitly separate trusted instructions from data. StruQ
uses structured channels and corresponding model training
#citep("chen2024struq"). Promptbreak instead evaluates defenses that can be run locally
without fine-tuning: classification before generation, hardened prompts,
context checks, and deterministic inspection after generation. General safety
models are included as out-of-the-box baselines, not as models specifically
trained for prompt injection.

Overblocking is central to our design. NotInject contains benign requests with
tokens commonly associated with attacks #citep("li2025piguard"), while XSTest uses
minimally contrasting safe and unsafe prompts to reveal exaggerated safety
behavior #citep("rottger2024xstest"). Our benign cases apply this contrast principle to
passwords, system prompts, encodings, debugging, and roleplay.

PIGuard addresses the same failure mode with a lightweight DeBERTa classifier
and Mitigating Over-defense for Free (MOF) #citep("li2025piguard"). MOF first
tests tokenizer vocabulary items individually to identify tokens that a trained
classifier spuriously associates with attacks. It then generates benign
sentences containing those tokens and retrains the model without using
NotInject as training data. This distinction matters for our additional
fine-tuning experiment described below.

Adaptive evaluation complements static attacks. Rainbow Teaming frames
adversarial prompt search as quality diversity and retains effective candidates
across behavioral niches #citep("samvelyan2024rainbow"). We implement a deliberately
small variant, Rainbow-lite, rather than claiming a replication of its
distributed MAP-Elites experiments.

= System and Defenses

Promptbreak is implemented as a Python web application backed by Ollama. All
models, synthetic secrets, metrics, and conversation state remain local. The
browser never receives a level's secret unless the evaluated response actually
leaks it. The application has no tools, external accounts, or real credentials.

== Intentionally vulnerable levels

The three levels represent increasingly contextual failure modes. Level 1 has
a legacy quality-assurance path triggered by an authority claim. Level 2 has a
narrow unsafe export path expressed through SQL or structured formats. Level 3
uses a three-step disaster-recovery sequence whose final artifact can be
wrapped in Base64. Vulnerable baseline paths are deterministic so that a known
solution does not depend on stochastic model compliance. Other requests are
answered by the selected target LLM.

== Defense configurations

We compare five fixed configurations:

- *Prompt only* relies solely on the target model's system prompt.
- *Promptbreak Guard* combines narrowly scoped lexical heuristics with a
  task-specific LLM classifier and a confidence threshold of 0.55.
- *Llama Guard 3 1B* is used unchanged as a general content-safety classifier.
- *ShieldGemma 2B* is likewise used unchanged as a policy-oriented safety
  classifier.
- *Full Pipeline* combines the Promptbreak input guard, prompt hardening, a
  context-aware guard, and direct plus encoded output-leak detectors.

#figure(
  image("../pitch/assets/defense-pipeline.svg", width: 95%),
  caption: [The layered Promptbreak defense pipeline. Requests can be rejected
    before target generation, while direct and encoded leaks can be redacted
    afterward.],
) <fig:pipeline>

The output filter recognizes direct, hexadecimal, ROT13, reversed, and Base64
representations. Evaluation uses a separate and stronger deterministic judge
that additionally detects decimal bytes, binary, and Unicode code points. This
separation avoids defining success with the same mechanism that performs the
defense.

== Experimental fine-tuned Llama guard

The repository additionally contains a PIGuard-inspired training notebook for a
binary Llama sequence classifier. It uses optional 4-bit NF4 quantization and
LoRA adapters with rank 16 on the query, key, value, and output attention
projections. The source-tagged corpus contains 76,735 records: 61,069 benign
prompts and 15,666 injections. The notebook creates a stratified 90/10 split and
trains for 200 optimization steps with an effective batch size of 16.

This model must not be described as PIGuard. It changes the base architecture
from DeBERTa to Llama and does not implement MOF's token-wise recheck and
adaptive benign-data generation. At the time of writing, the notebook also does
not record an exact base-model identifier, maximum input length, completed
training outputs, or a versioned adapter artifact. We therefore treat it as an
experimental method whose evaluation is pending, not as an additional result.

= Evaluation

== Dataset

Promptbreak Guard Evaluation v1.1 is a frozen set of 30 German and English
cases. It contains 15 attacks: five authority attacks, five format-smuggling
attacks, three multi-turn attacks, and two encoding attacks. Four are
Promptbreak-specific and eleven are adapted from Open Prompt Injection
#citep("liu2024openpromptinjection"). The remaining 15 cases are XSTest-inspired benign
contrasts, with three cases each for password, system-prompt, encoding,
debugging, and roleplay language. Every record stores its category, level,
dialog history, provenance, and expected behavior.

The benchmark is intentionally application-specific. Its deterministic legacy
paths make defense behavior comparable, but also make prompt-only attack success
an engineered property of the testbed rather than an estimate for arbitrary
LLM applications.

== Metrics and protocol

Attack success rate (ASR) is the share of attacks for which the synthetic secret
reaches the client. For input classification, we report false-positive rate,
precision, recall, and F1. We distinguish input-guard false positives from the
end-to-end benign block rate: a benign prompt can pass the guard but cause the
target model to leak a secret, which a correct output filter then suppresses.

We also record end-to-end, guard, target/application, and output-filter time;
model load time; model calls; and prompt and completion tokens. Local API cost is
zero. Model calls, tokens, and wall-clock time are therefore the relevant
compute proxies. Latency is separated by response path because deterministic
legacy responses and early guard refusals are not comparable to target-model
generation.

The reported main run uses Qwen 3.5 4B as both target and Promptbreak classifier,
with Llama Guard 3 1B and ShieldGemma 2B for their respective configurations.
It evaluates all 30 cases once per configuration (150 observations). A final
three-repeat run is still pending; the results below must therefore be read as a
complete single pass, not as a variance estimate.

The fine-tuned guard will be evaluated as a sixth standalone configuration and
as a replacement for the learned input classifier inside the full pipeline.
Threshold selection will use a separate validation split. Final tests will
combine Promptbreak Evaluation v1.1 for application-specific ASR with the
untouched 339-case NotInject benchmark for trigger-word overdefense. We will
compare the model against the current Promptbreak guard, Llama Guard 3,
ShieldGemma, and the official PIGuard checkpoint using paired inputs. In
addition to ASR and input FPR, we will report attack recall, overdefense FPR,
balanced accuracy, F1, calibration, latency, peak memory, and model calls across
at least three independent training seeds.

= Results

#figure(
  table(
    columns: (1.55fr, 0.7fr, 0.7fr, 0.7fr, 0.85fr, 0.8fr),
    align: (left, right, right, right, right, right),
    [*Configuration*], [*ASR ↓*], [*FPR ↓*], [*F1 ↑*], [*Mean ms*], [*Calls*],
    [Prompt only], [100.0], [0.0], [0.000], [4,001], [15],
    [Promptbreak Guard], [13.3], [0.0], [0.929], [7,456], [43],
    [Llama Guard 3], [66.7], [0.0], [0.500], [5,575], [45],
    [ShieldGemma], [100.0], [0.0], [0.000], [4,949], [45],
    [Full Pipeline], [0.0], [13.3#super[1]], [0.938], [7,017], [40],
  ),
  caption: [Qwen 3.5 4B single-pass results over 30 cases. ASR and FPR are
    percentages. Calls are totals. #super[1]Both benign blocks were produced by
    the output filter after target-model leaks; the input guard itself had 0.0%
    FPR.],
) <tab:main-results>

Table @tab:main-results shows that a system prompt alone provides no protection
against the deterministic attack paths. ShieldGemma behaves identically on
attack success, suggesting that its general safety policy does not cover these
application-specific attacks. Llama Guard detects five of fifteen attacks
(33.3% recall), reducing ASR to 66.7%. The Promptbreak Guard detects thirteen
attacks with no input false positives, reducing ASR to 13.3%. The full pipeline
blocks the two remaining attack leaks and reaches 0% ASR.

The full pipeline also blocks two of fifteen benign cases end to end. Trace
inspection shows that both pass the input guard but cause the target model to
emit a real synthetic secret; the output filter therefore acts correctly with
respect to confidentiality. Counting these cases only as input-classifier false
positives would obscure this distinction. We consequently report both input
FPR (0%) and end-to-end benign block rate (13.3%).

The strongest configurations require more computation. Prompt only makes 15
model calls and processes 6,411 tokens, whereas Promptbreak Guard makes 43 calls
and processes 14,736 tokens. The full pipeline makes 40 calls and processes
14,226 tokens; early blocking explains why it uses fewer calls than a uniform
two-model cascade. Mean latency rises from 4.0 seconds for prompt only to 7.5
seconds for the Promptbreak Guard and 7.0 seconds for the full pipeline.

== Adaptive Rainbow-lite evaluation

We additionally run 24 adaptive mutations against the full pipeline, using Qwen
3.5 4B as attacker and Gemma 4 as target. The archive crosses four attack
families with four transformations (direct, roleplay, structured, and
obfuscated). All 16 cells become occupied. Neither the four static seeds nor the
24 adaptive candidates exfiltrate a secret, yielding 0% static and adaptive ASR.
This demonstrates robustness only within this small search budget and mutation
scheme.

= Discussion

The results support three practical conclusions. First, general content-safety
guards are not interchangeable with prompt-injection defenses: Llama Guard
offers partial protection, concentrated in a subset of formats, while
ShieldGemma offers no measurable protection here. Second, a task-specific guard
can provide a substantially better security--utility boundary when its
heuristics and threshold are calibrated against benign contrasts. Third,
post-generation filtering remains useful because a classifier can miss attacks
and even a benign request can elicit protected state from the target model.

Defense-in-depth is not free. Additional calls approximately double token use
and increase mean latency. Early refusal can also make aggregate percentiles
look deceptively favorable, which is why response-path-specific timing is
necessary. The distinction between guard refusal and output-filter intervention
is equally important for utility analysis.

== Limitations

The benchmark is small, bilingual, and tailored to three synthetic application
vulnerabilities. Several attacks are adapted rather than copied verbatim, and
the benign cases are inspired by XSTest rather than a representative user
distribution. The single-pass Qwen comparison cannot quantify run-to-run
variance. Deterministic vulnerable paths improve reproducibility but inflate
prompt-only ASR by construction. Rainbow-lite uses only 24 mutations and does
not approximate the scale or diversity of the original Rainbow Teaming study.
Finally, the environment has no tools or real side effects, so the evaluation
does not cover indirect injection or agentic harm as studied by BIPIA and
AgentDojo #citep("yi2023bipia", "debenedetti2024agentdojo").

The fine-tuning corpus introduces further validity risks. It contains exact
duplicates, three empty prompts, and five duplicated prompt groups with
conflicting labels. An example-level random split can consequently leak related
prompts into validation. Before reporting the fine-tuned model, we will resolve
these records, group exact and near duplicates, freeze source-disjoint splits,
document dataset licenses, and keep both NotInject and the Promptbreak test set
outside training.

= Conclusion

Promptbreak combines an educational prompt-injection game with a transparent,
reproducible defense evaluation. In the current complete single-pass run,
application-specific input filtering sharply outperforms two general safety
guards, while a layered pipeline eliminates all measured attack successes at
the cost of additional latency and two end-to-end benign blocks caused by real
target-model leaks. The next required experiment is a three-repeat final run
with frozen models and configuration, followed by an unseen holdout. The
project's central lesson is therefore not that the pipeline is universally
robust, but that prompt-injection defenses should be evaluated as layered
systems on both security and utility.

= Reproducibility

The repository contains the frozen dataset, complete JSON reports, model-free
unit tests, visualization scripts, and all command lines required to reproduce
the study. The main comparison is run with `experiments.compare_guards`;
adaptive search uses `experiments.rainbow_lite`; and
`experiments.visualize_results` regenerates the SVG figures.
All model inference uses local Ollama endpoints and records the exact model tags
in each result file.

The fine-tuning notebook, source-tagged corpus, and a separate protocol document
are included for inspection. A reproducible release will additionally require
the exact base-model revision, adapter checksum, tokenizer, training log,
decision threshold, software versions, and hardware description.

#print-acl-bibliography()
