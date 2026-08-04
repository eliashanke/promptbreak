"""Small Ollama model registry used by the reproducible evaluations.

The benchmark accepts both the short aliases below and arbitrary Ollama tags.
Profiles only describe request-time differences; no model is downloaded here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class OllamaModelProfile:
    alias: str
    ollama_tag: str
    family: str
    organization: str
    parameter_class: str
    download_gb: float
    context_tokens: int
    thinking: bool = False
    note: str = ""


MODEL_PROFILES: Dict[str, OllamaModelProfile] = {
    "gemma4": OllamaModelProfile(
        alias="gemma4",
        ollama_tag="gemma4:latest",
        family="Gemma 4",
        organization="Google DeepMind",
        parameter_class="E4B (8B including embeddings)",
        download_gb=9.6,
        context_tokens=131_072,
        note="Existing project baseline.",
    ),
    "qwen35_9b": OllamaModelProfile(
        alias="qwen35_9b",
        ollama_tag="qwen3.5:9b",
        family="Qwen 3.5",
        organization="Alibaba Cloud / Qwen",
        parameter_class="9B",
        download_gb=6.6,
        context_tokens=262_144,
        thinking=True,
        note="Recommended modern Chinese comparison model.",
    ),
    "qwen3_14b": OllamaModelProfile(
        alias="qwen3_14b",
        ollama_tag="qwen3:14b",
        family="Qwen 3",
        organization="Alibaba Cloud / Qwen",
        parameter_class="14B",
        download_gb=9.3,
        context_tokens=40_960,
        thinking=True,
        note="Closest match to gemma4:latest by Ollama download size.",
    ),
    "deepseek_r1_14b": OllamaModelProfile(
        alias="deepseek_r1_14b",
        ollama_tag="deepseek-r1:14b",
        family="DeepSeek R1 Distill Qwen",
        organization="DeepSeek",
        parameter_class="14B",
        download_gb=9.0,
        context_tokens=131_072,
        thinking=True,
        note="Reasoning-oriented Chinese comparison model.",
    ),
    "glm4_9b": OllamaModelProfile(
        alias="glm4_9b",
        ollama_tag="glm4:9b",
        family="GLM-4",
        organization="Zhipu AI / THUDM",
        parameter_class="9B",
        download_gb=5.5,
        context_tokens=131_072,
        note="Older and smaller optional multilingual comparison.",
    ),
}


DEFAULT_TARGET_MODEL_ALIASES = ("gemma4", "qwen35_9b", "qwen3_14b", "deepseek_r1_14b")


def resolve_model_tag(model: str) -> str:
    """Resolve a registry alias while leaving normal Ollama tags untouched."""
    profile = MODEL_PROFILES.get(model)
    return profile.ollama_tag if profile else model


def request_overrides(model: str) -> Dict[str, Any]:
    """Return deterministic request options for model-family quirks.

    Qwen 3/3.5 and DeepSeek R1 enable reasoning by default in recent Ollama
    versions. The benchmark disables it so completion tokens and latency measure
    the same task rather than a variable-length hidden reasoning trace.
    """
    resolved = resolve_model_tag(model).lower()
    profile = MODEL_PROFILES.get(model)
    is_thinking_model = bool(profile and profile.thinking) or resolved.startswith(
        ("qwen3:", "qwen3.5:", "deepseek-r1:")
    )
    return {"think": False} if is_thinking_model else {}


def describe_model(model: str) -> Dict[str, Any]:
    """Return serializable metadata for reports, including unknown raw tags."""
    profile = MODEL_PROFILES.get(model)
    if profile:
        return asdict(profile)
    return {
        "alias": None,
        "ollama_tag": resolve_model_tag(model),
        "family": "custom",
        "organization": "unknown",
        "parameter_class": "unknown",
        "download_gb": None,
        "context_tokens": None,
        "thinking": bool(request_overrides(model)),
        "note": "User-supplied Ollama tag.",
    }
