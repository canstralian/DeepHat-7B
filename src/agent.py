"""Agent layers for DeepHat generation and local security triage tools."""

from __future__ import annotations

import re
from queue import Empty, Queue
from threading import Thread
from typing import Any, Callable, Iterable

from src.tools.artifact_store import store_artifact
from src.tools.code_lint import format_lint_results, lint_code
from src.tools.code_test import analyze_python_code, format_code_test_result
from src.tools.cve_lookup import format_cve_results, lookup_cves
from src.tools.dataset_search import format_dataset_results, search_datasets
from src.tools.eval_runner import format_eval_results, run_evals
from src.tools.model_registry_lookup import model_registry_lookup
from src.tools.policy_check import check_policy, format_policy_results


ToolHandler = Callable[[str], str]
Message = dict[str, str]


class DeepHatAgent:
    """Lazy-loading wrapper around the configured DeepHat-compatible model."""

    def __init__(
        self,
        model_id: str = "DeepHat/DeepHat-V1-7B",
        device: str = "auto",
        load_in_4bit: bool = False,
    ) -> None:
        self.model_id = model_id
        self.device = device
        self.load_in_4bit = load_in_4bit
        self._tokenizer: Any | None = None
        self._model: Any | None = None

    @property
    def tokenizer(self) -> Any:
        self._ensure_model_loaded()
        return self._tokenizer

    @property
    def model(self) -> Any:
        self._ensure_model_loaded()
        return self._model

    def generate(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_new_tokens: int = 2048,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
    ) -> str:
        """Generate a complete response."""

        return "".join(
            self.generate_stream(
                messages=messages,
                temperature=temperature,
                max_new_tokens=max_new_tokens,
                top_p=top_p,
                repetition_penalty=repetition_penalty,
            )
        )

    def generate_stream(
        self,
        messages: list[Message],
        temperature: float = 0.7,
        max_new_tokens: int = 2048,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
    ) -> Iterable[str]:
        """Yield generated text chunks using Transformers streaming when available."""

        self._ensure_model_loaded()
        inputs = self._encode_messages(messages)
        inputs = self._move_inputs_to_model_device(inputs)

        try:
            import torch
            from transformers import TextIteratorStreamer
        except ImportError as exc:
            raise RuntimeError(
                "DeepHat generation requires torch and transformers. "
                "Install requirements.txt before running model inference."
            ) from exc

        streamer = TextIteratorStreamer(
            self._tokenizer,
            skip_prompt=True,
            skip_special_tokens=True,
            timeout=1.0,
        )
        generation_errors: Queue[BaseException] = Queue(maxsize=1)
        generation_kwargs = {
            **inputs,
            "streamer": streamer,
            "max_new_tokens": max_new_tokens,
            "temperature": max(temperature, 1e-5),
            "top_p": top_p,
            "repetition_penalty": repetition_penalty,
            "do_sample": temperature > 0,
            "pad_token_id": self._tokenizer.pad_token_id,
            "eos_token_id": self._tokenizer.eos_token_id,
        }

        def run_generation() -> None:
            try:
                with torch.inference_mode():
                    self._model.generate(**generation_kwargs)
            except BaseException as exc:  # pragma: no cover - surfaced after thread exits.
                generation_errors.put(exc)

        thread = Thread(target=run_generation, daemon=True)
        thread.start()
        while True:
            try:
                chunk = next(streamer)
            except StopIteration:
                break
            except Empty:
                if not generation_errors.empty():
                    break
                if not thread.is_alive():
                    break
                continue
            if chunk:
                yield chunk
        thread.join()

        if not generation_errors.empty():
            raise generation_errors.get()

    def _ensure_model_loaded(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "DeepHat generation requires torch and transformers. "
                "Install requirements.txt before running model inference."
            ) from exc

        tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            trust_remote_code=True,
            padding_side="left",
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token

        model_kwargs: dict[str, Any] = {
            "trust_remote_code": True,
            "low_cpu_mem_usage": True,
        }
        if self.device == "cpu":
            model_kwargs["torch_dtype"] = torch.float32
        else:
            model_kwargs["torch_dtype"] = torch.bfloat16
            model_kwargs["device_map"] = "auto" if self.device == "auto" else {"": self.device}

        if self.load_in_4bit:
            try:
                from transformers import BitsAndBytesConfig
            except ImportError as exc:
                raise RuntimeError("4-bit loading requires bitsandbytes support.") from exc
            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )

        model = AutoModelForCausalLM.from_pretrained(self.model_id, **model_kwargs)
        if self.device == "cpu":
            model = model.to("cpu")
        model.eval()

        self._tokenizer = tokenizer
        self._model = model

    def _encode_messages(self, messages: list[Message]) -> Any:
        try:
            return self._tokenizer.apply_chat_template(
                messages,
                tokenize=True,
                return_tensors="pt",
                return_dict=True,
                add_generation_prompt=True,
            )
        except (AttributeError, TypeError):
            prompt = self._fallback_chat_prompt(messages)
            return self._tokenizer(prompt, return_tensors="pt")

    def _move_inputs_to_model_device(self, inputs: Any) -> Any:
        model_device = getattr(self._model, "device", None)
        if model_device is None:
            try:
                model_device = next(self._model.parameters()).device
            except (AttributeError, StopIteration):
                model_device = None
        if model_device is not None and hasattr(inputs, "to"):
            return inputs.to(model_device)
        return inputs

    @staticmethod
    def _fallback_chat_prompt(messages: list[Message]) -> str:
        lines = []
        for message in messages:
            role = message.get("role", "user").strip().title()
            content = message.get("content", "").strip()
            if content:
                lines.append(f"{role}: {content}")
        lines.append("Assistant:")
        return "\n".join(lines)


class SecurityAssistantAgent:
    """Small local agent that routes prompts to explicit deterministic tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolHandler] = {
            "dataset_search": self._dataset_search,
            "model_registry_lookup": self._model_registry_lookup,
            "cve_lookup": self._cve_lookup,
            "code_lint": self._code_lint,
            "code_test": self._code_test,
            "policy_check": self._policy_check,
            "artifact_store": self._artifact_store,
            "eval_runner": self._eval_runner,
        }

    @property
    def tool_names(self) -> tuple[str, ...]:
        return tuple(self._tools)

    def respond(self, message: str, tool: str = "auto") -> str:
        """Return a Markdown response for a user request."""

        normalized_message = (message or "").strip()
        if not normalized_message:
            return (
                "Provide a CVE, dataset/model query, code snippet, policy text, "
                "or evaluation request."
            )

        selected_tool = self._select_tool(normalized_message, tool)
        handler = self._tools.get(selected_tool)
        if handler is None:
            available = ", ".join(("auto", *self.tool_names))
            return f"Unknown tool `{tool}`. Available tools: {available}."

        result = handler(normalized_message)
        return f"**Tool:** `{selected_tool}`\n\n{result}"

    def generate(self, prompt: str) -> str:
        """Compatibility entrypoint for older Space app.py versions."""

        return self.respond(prompt, "auto")

    def _select_tool(self, message: str, requested_tool: str) -> str:
        requested_tool = (requested_tool or "auto").strip()
        if requested_tool != "auto":
            return requested_tool

        lower_message = message.lower()
        if re.search(r"\bcve-\d{4}-\d{4,}\b", lower_message) or any(
            keyword in lower_message for keyword in ("cve", "log4j", "openssl", "struts", "moveit")
        ):
            return "cve_lookup"
        if any(
            keyword in lower_message
            for keyword in ("lint", "vulnerability in code", "security issue in code")
        ):
            return "code_lint"
        if any(
            keyword in lower_message
            for keyword in ("pytest", "unit test", "syntax", "run tests", "test this code", "test code")
        ):
            return "code_test"
        if "```" in message or any(keyword in lower_message for keyword in ("shell=true", "eval(", "exec(")):
            return "code_lint"
        if any(keyword in lower_message for keyword in ("dataset", "benchmark", "corpus")):
            return "dataset_search"
        if any(keyword in lower_message for keyword in ("model", "registry", "llm")):
            return "model_registry_lookup"
        if any(keyword in lower_message for keyword in ("policy", "compliance", "governance", "control")):
            return "policy_check"
        if any(keyword in lower_message for keyword in ("eval", "evaluation", "test cases")):
            return "eval_runner"
        return "policy_check"

    def _dataset_search(self, message: str) -> str:
        return format_dataset_results(search_datasets(message))

    def _model_registry_lookup(self, message: str) -> str:
        return model_registry_lookup(message, [])

    def _cve_lookup(self, message: str) -> str:
        return format_cve_results(lookup_cves(message))

    def _code_lint(self, message: str) -> str:
        return format_lint_results(lint_code(_extract_code(message)))

    def _code_test(self, message: str) -> str:
        return format_code_test_result(analyze_python_code(_extract_code(message)))

    def _policy_check(self, message: str) -> str:
        return format_policy_results(check_policy(message))

    def _artifact_store(self, message: str) -> str:
        artifact = store_artifact(message)
        return f"Stored artifact `{artifact.name}` at `{artifact.path}`."

    def _eval_runner(self, message: str) -> str:
        return format_eval_results(run_evals(self.respond))


def _extract_code(message: str) -> str:
    """Prefer the first fenced code block, otherwise return the full message."""

    match = re.search(r"```(?:\w+)?\s*(.*?)```", message, re.DOTALL)
    if match:
        return match.group(1).strip()
    return message.strip()


SecurityAgent = SecurityAssistantAgent
