"""Lazy local inference for the PEFT sequence-classification guard."""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ADAPTER_PATH = ROOT / "finetuning" / "checkpoint-650"
ADAPTER_ENV = "PROMPTBREAK_FINETUNED_GUARD_PATH"

_LOAD_LOCK = threading.Lock()
_LOADED: tuple[Any, Any, Any, str, Path] | None = None


def adapter_path() -> Path:
    configured = os.environ.get(ADAPTER_ENV)
    return Path(configured).expanduser().resolve() if configured else DEFAULT_ADAPTER_PATH


def adapter_metadata() -> dict[str, Any]:
    path = adapter_path()
    config_path = path / "adapter_config.json"
    metadata: dict[str, Any] = {
        "id": "finetuned",
        "label": "Fine-tuned Llama guard",
        "available": config_path.is_file() and (path / "adapter_model.safetensors").is_file(),
    }
    if config_path.is_file():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        metadata["baseModel"] = config.get("base_model_name_or_path")
        metadata["taskType"] = config.get("task_type")
    return metadata


def _load() -> tuple[Any, Any, Any, str, Path]:
    global _LOADED
    if _LOADED is not None:
        return _LOADED
    with _LOAD_LOCK:
        if _LOADED is not None:
            return _LOADED
        path = adapter_path()
        if not adapter_metadata()["available"]:
            raise RuntimeError(
                f"Fine-tuned guard adapter not found at {path}. "
                f"Set {ADAPTER_ENV} to a PEFT adapter directory."
            )
        try:
            import torch
            from peft import PeftConfig, PeftModel
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "Fine-tuning dependencies are missing; run `uv sync --group finetuning`."
            ) from exc

        peft_config = PeftConfig.from_pretrained(path)
        base_model_name = str(peft_config.base_model_name_or_path)
        tokenizer = AutoTokenizer.from_pretrained(path)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        model = AutoModelForSequenceClassification.from_pretrained(
            base_model_name,
            num_labels=2,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        )
        model.config.pad_token_id = tokenizer.pad_token_id
        model = PeftModel.from_pretrained(model, path)
        model.to(device)
        model.eval()
        _LOADED = tokenizer, model, torch, device, path
        return _LOADED


def classify(text: str) -> dict[str, Any]:
    """Return the probability that *text* is a prompt injection (label 1)."""
    tokenizer, model, torch, device, path = _load()
    encoded = tokenizer(text, truncation=True, max_length=256, return_tensors="pt")
    token_count = int(encoded["input_ids"].shape[-1])
    encoded = {key: value.to(device) for key, value in encoded.items()}
    with torch.inference_mode():
        logits = model(**encoded).logits
        probability = float(torch.softmax(logits.float(), dim=-1)[0, 1].item())
    return {
        "confidence": probability,
        "tokenCount": token_count,
        "model": str(path),
        "device": device,
    }
