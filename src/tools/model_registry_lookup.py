"""DeepHat model lookup with lazy loading and offline fallback helpers."""

from __future__ import annotations

import os
from contextlib import nullcontext
from dataclasses import dataclass
from functools import lru_cache
from typing import Any


DEFAULT_MODEL_ID = "DeepHat/DeepHat-V1-7B"


@dataclass(frozen=True)
class ModelRecord:
    name: str
    family: str
    recommended_use: str
    review_notes: str
    tags: tuple[str, ...]


MODELS: tuple[ModelRecord, ...] = (
    ModelRecord(
        name="Llama Guard",
        family="Safety classifier",
        recommended_use="Content safety classification and policy gating.",
        review_notes="Treat output as one signal; keep human review for high-impact decisions.",
        tags=("guard", "safety", "classifier", "policy"),
    ),
    ModelRecord(
        name="Code Llama",
        family="Code generation",
        recommended_use="Code assistance and review drafts in controlled workflows.",
        review_notes="Do not accept generated patches without tests and human review.",
        tags=("code", "llm", "generation", "review"),
    ),
    ModelRecord(
        name="StarCoder2",
        family="Code generation",
        recommended_use="Repository-aware code generation and explanation tasks.",
        review_notes="Check license, provenance, and secret leakage risks before deployment.",
        tags=("code", "llm", "repository"),
    ),
    ModelRecord(
        name="DistilBERT",
        family="Text classification",
        recommended_use="Lightweight classification baselines and routing models.",
        review_notes="Validate against domain-specific false positive and false negative costs.",
        tags=("classification", "baseline", "text"),
    ),
)


def lookup_models(query: str, limit: int = 3) -> list[ModelRecord]:
    tokens = _query_tokens(query)
    if not tokens:
        return list(MODELS[:limit])

    scored: list[tuple[int, ModelRecord]] = []
    for model in MODELS:
        haystack = " ".join(
            (
                model.name,
                model.family,
                model.recommended_use,
                model.review_notes,
                " ".join(model.tags),
            )
        ).lower()
        score = sum(1 for token in tokens if token in haystack)
        if score:
            scored.append((score, model))

    scored.sort(key=lambda item: (-item[0], item[1].name))
    return [model for _, model in scored[:limit]]


def format_model_results(results: list[ModelRecord]) -> str:
    if not results:
        return "No local model records matched. Try terms like `code`, `safety`, or `classification`."

    lines = ["### Model Registry Matches"]
    for record in results:
        lines.extend(
            (
                f"- **{record.name}** ({record.family})",
                f"  - Recommended use: {record.recommended_use}",
                f"  - Review notes: {record.review_notes}",
            )
        )
    return "\n".join(lines)


def _query_tokens(query: str) -> set[str]:
    return {token for token in query.lower().replace("-", " ").split() if len(token) > 2}


@lru_cache(maxsize=1)
def load_model() -> tuple[Any, Any]:
    """Load the configured language model once per process."""

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "DeepHat generation requires torch and transformers. "
            "Install requirements.txt before using model_registry_lookup."
        ) from exc

    model_id = os.getenv("MODEL_ID", DEFAULT_MODEL_ID)
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        trust_remote_code=True,
        torch_dtype="auto",
        device_map="auto",
        low_cpu_mem_usage=True,
    )
    model.eval()
    return tokenizer, model


def model_registry_lookup(prompt: str, context: list[dict[str, Any]] | None = None) -> str:
    """Query DeepHat with retrieved context."""

    tokenizer, model = load_model()
    formatted_prompt = _format_prompt(prompt, context or [])
    inputs = tokenizer(formatted_prompt, return_tensors="pt")
    model_device = getattr(model, "device", None)
    if model_device is not None and hasattr(inputs, "to"):
        inputs = inputs.to(model_device)

    with _inference_context():
        outputs = model.generate(
            **inputs,
            max_new_tokens=int(os.getenv("MAX_NEW_TOKENS", "256")),
            do_sample=os.getenv("DO_SAMPLE", "false").lower() == "true",
            pad_token_id=tokenizer.eos_token_id,
        )

    prompt_tokens = inputs["input_ids"].shape[-1]
    generated_tokens = outputs[0][prompt_tokens:]
    return tokenizer.decode(generated_tokens, skip_special_tokens=True).strip()


def _format_prompt(prompt: str, context: list[dict[str, Any]]) -> str:
    return f"Context: {context}\n\nQuestion: {prompt}\nAnswer:"


def _inference_context():
    try:
        import torch
    except ImportError:
        return nullcontext()
    return torch.inference_mode()
