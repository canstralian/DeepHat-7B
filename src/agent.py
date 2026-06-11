"""Deterministic routing layer for local security assistant tools."""

from __future__ import annotations

import re
from typing import Callable

from src.tools.artifact_store import store_artifact
from src.tools.code_lint import format_lint_results, lint_code
from src.tools.code_test import analyze_python_code, format_code_test_result
from src.tools.cve_lookup import format_cve_results, lookup_cves
from src.tools.dataset_search import format_dataset_results, search_datasets
from src.tools.eval_runner import format_eval_results, run_evals
from src.tools.model_registry_lookup import model_registry_lookup
from src.tools.policy_check import check_policy, format_policy_results


ToolHandler = Callable[[str], str]


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
