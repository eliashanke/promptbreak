# Fine-tuned Llama prompt-injection guard

## Status and scope

`finetuning/overfiltering.ipynb` contains an experimental recipe for adapting a
Llama sequence-classification model to distinguish benign prompts (`label = 0`)
from prompt injections (`label = 1`). The motivation and training corpus are based
on the official [PIGuard repository](https://github.com/leolee99/PIGuard/tree/main)
and the ACL 2025 paper [*PIGuard: Prompt Injection Guardrail via Mitigating
Overdefense for Free*](https://aclanthology.org/2025.acl-long.1468/).

This experiment is **PIGuard-inspired, not a reproduction of PIGuard**.
PIGuard uses a lightweight DeBERTa classifier and its Mitigating Over-defense
for Free (MOF) procedure. MOF checks every tokenizer vocabulary item in
isolation, identifies tokens that the initial classifier spuriously considers
malicious, generates benign training sentences containing those tokens, and
retrains the classifier. The current Promptbreak notebook instead fine-tunes a
Llama sequence classifier with 4-bit quantization and LoRA. It does not contain
PIGuard's token-wise recheck or MOF data-generation stage.

## Current implementation

The notebook performs the following operations:

1. Load `data/finetuning/train.json` and map `prompt` to the model input and
   `label` to a binary classification target.
2. Create a stratified random 90/10 train/evaluation split with seed 42.
3. Tokenize with truncation at `MAX_LENGTH` and dynamically pad each batch.
4. Optionally load the base model in 4-bit NF4 format.
5. Add LoRA adapters to the attention projections `q_proj`, `k_proj`, `v_proj`,
   and `o_proj`, using rank 16, alpha 32, and dropout 0.05.
6. Optimize for one epoch with an effective batch size of 16, learning rate
   5e-5, cosine scheduling, 6% warm-up, FP16, gradient checkpointing, and
   `paged_adamw_32bit`.
7. Report accuracy, binary precision, recall, and F1 on the notebook's
   evaluation split and save the final LoRA adapter.

The checked-in `data/finetuning/train.json` contains 76,735 records from 22
named sources: 61,069 benign examples (79.6%) and 15,666 injections (20.4%).
The file includes three empty prompts, 2,366 groups of duplicated prompt
strings, and five prompt groups with conflicting labels. No exact prompt from
Promptbreak Evaluation v1.1 occurs in the training file. The dataset is stored
with Git LFS because of its size.

`finetuning/training_log_history.json` contains 700 recorded training steps and
13 validation runs through step 650. The best recorded validation F1 is 0.9382
at step 600. These metrics are displayed in the web dashboard, but remain
diagnostic because the random split has not yet been made leakage-safe.

## Local environment and application integration

Install the notebook and inference dependencies with:

```bash
uv sync --group finetuning
```

The group pins `transformers==5.13.1` and includes PyTorch, Datasets, PEFT,
Accelerate, bitsandbytes, scikit-learn, NumPy, and IPykernel. The web app loads
the PEFT adapter lazily only when **Fine-tuned Llama guard** is selected. By
default it looks for `finetuning/checkpoint-650`; override the location with:

```bash
PROMPTBREAK_FINETUNED_GUARD_PATH=/absolute/path/to/adapter \
  uv run python -m promptbreak
```

The base model is `meta-llama/Llama-3.2-1B`. It must be accessible through the
local Hugging Face cache or an authenticated Hugging Face account. The first
classification loads the base model and adapter and is therefore considerably
slower than subsequent requests.

Ollama can import supported Llama Safetensors and LoRA adapters for generative
models, but this adapter is a `SEQ_CLS` PEFT model with a trained classification
head. Promptbreak therefore performs inference directly with Transformers and
PyTorch instead of sending it through Ollama's chat/generate API. Ollama remains
responsible for the target model and the existing generative guards.

## Reproducibility gaps

The notebook is currently a training draft, not a self-contained reproducible
artifact:

- `MODEL_NAME`, `MAX_LENGTH`, `USE_4BIT`, and `OUTPUT_DIR` are referenced but
  not defined in a checked-in configuration cell.
- notebook cells have empty execution counts and no embedded output
- a local adapter and tokenizer checkpoint exists at `finetuning/checkpoint-650`
  but is intentionally ignored because it is a large generated artifact
- the training log is versioned, but the final selected adapter, decision
  threshold, and external test predictions are not frozen
- base-model revision, package versions, hardware, training seed, and adapter
  checksum are not recorded
- `data/finetuning/train.json` lists source names but does not yet provide
  per-source URLs,
  versions, licenses, or transformation notes
- an example-level random split can place duplicate or near-duplicate prompts
  in both training and validation data

Before reporting a result, define and save the missing configuration, remove or
resolve empty and conflicting records, deduplicate before splitting, and split
by normalized prompt group and preferably by source or attack family.

## Required evaluation

### 1. Freeze the artifact and threshold

Record the exact base-model identifier and revision, tokenizer, adapter files,
maximum length, label mapping, random seed, software versions, GPU, training
duration, and SHA-256 checksums. Select the malicious-class threshold on a
dedicated validation set. Do not tune the threshold on any reported test set.

### 2. Evaluate classification independently

Use mutually exclusive test sets for three distinct capabilities:

- **malicious detection:** unseen direct, format-smuggling, multi-turn, and
  encoding attacks
- **ordinary benign accuracy:** benign prompts without deliberately planted
  injection vocabulary
- **overdefense:** the complete 339-case NotInject benchmark or another
  untouched trigger-rich benign set

Report the confusion matrix, attack recall, benign false-positive rate,
overdefense false-positive rate, precision, F1, balanced accuracy, Matthews
correlation coefficient, AUROC, AUPRC, and calibration. Because the training
set is imbalanced, accuracy alone is insufficient. Break results down by source,
language, attack family, number of trigger words, and input-length bucket.

### 3. Add a paired Promptbreak comparison

Add the fine-tuned classifier as a sixth configuration in
`experiments/compare_guards.py`
and evaluate the same inputs in the same order against:

- Prompt only
- the current Promptbreak heuristic + LLM guard
- Llama Guard 3 1B
- ShieldGemma 2B
- the official `leolee99/PIGuard` checkpoint
- the fine-tuned Llama guard

Test the fine-tuned model both as a standalone input guard and as a replacement
for the learned classifier inside the full pipeline. Keep heuristics off in the
standalone condition so their contribution is not attributed to the model.

Report both classifier and application outcomes: input-guard FPR, input attack
recall, end-to-end benign block rate, secret-exfiltration ASR, mean/p50/p95
latency, peak memory, model calls, and token count. A classifier can correctly
allow a benign request whose target-model response is later blocked for leaking
a secret, so input FPR and end-to-end benign blocking must remain separate.

### 4. Prevent leakage and quantify uncertainty

Use exact and normalized near-duplicate checks across all splits. Keep
Promptbreak Evaluation v1.1 and NotInject out of training if they are used as
final tests. Run at least three independent training seeds. For the paired test
predictions, report bootstrap confidence intervals and use McNemar's test when
comparing error rates. The 30-case Promptbreak suite is too small to establish a
general improvement on its own.

### 5. Stress-test the selected model

After selecting one frozen checkpoint and threshold, run:

- the final 30 × configurations × 3 Promptbreak benchmark
- the complete held-out NotInject set, split by one, two, and three trigger
  words
- paraphrased and multilingual benign contrasts
- long-input tests around and beyond `MAX_LENGTH`
- Rainbow-lite against the full pipeline with the fine-tuned classifier
- threshold curves showing the attack-recall/overdefense-FPR trade-off

## Decision rule

The fine-tuned guard should be considered an improvement only if it reduces
overdefense on an unseen trigger-rich test set without a practically important
loss in malicious recall or end-to-end ASR. The current 15 benign Promptbreak
cases already yield 0% input-guard FPR for the tuned Qwen guard, so they cannot
by themselves demonstrate an overblocking improvement; a larger untouched
NotInject-style test is essential.

## Attribution

When presenting the model, use wording such as:

> We trained a PIGuard-inspired Llama sequence classifier with QLoRA on the
> open-source corpus distributed with PIGuard. Our implementation changes the
> base architecture and optimization method and does not reproduce PIGuard's
> MOF training procedure.

Retain the PIGuard paper citation and repository link, and document the licenses
and provenance of every retained source in `data/finetuning/train.json` before
publishing the adapter or redistributed training data.
