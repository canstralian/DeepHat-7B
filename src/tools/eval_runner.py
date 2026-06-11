"""Evaluation runner for local JSON test cases."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class EvalCase:
    name: str
    prompt: str
    tool: str
    expected_contains: str


@dataclass(frozen=True)
class EvalResult:
    name: str
    passed: bool
    expected_contains: str


DEFAULT_CASES_PATH = Path(__file__).resolve().parents[2] / "evals" / "test_cases.json"


def load_test_cases(path: Path = DEFAULT_CASES_PATH) -> list[EvalCase]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [
        EvalCase(
            name=item["name"],
            prompt=item["prompt"],
            tool=item.get("tool", "auto"),
            expected_contains=item["expected_contains"],
        )
        for item in data
    ]


def run_evals(responder: Callable[[str, str], str], path: Path = DEFAULT_CASES_PATH) -> list[EvalResult]:
    results: list[EvalResult] = []
    for case in load_test_cases(path):
        response = responder(case.prompt, case.tool)
        results.append(
            EvalResult(
                name=case.name,
                passed=case.expected_contains.lower() in response.lower(),
                expected_contains=case.expected_contains,
            )
        )
    return results


def format_eval_results(results: list[EvalResult]) -> str:
    if not results:
        return "No evaluation cases found."

    passed_count = sum(1 for result in results if result.passed)
    lines = [f"### Evaluation Results: {passed_count}/{len(results)} passed"]
    for result in results:
        status = "passed" if result.passed else "failed"
        lines.append(f"- **{status}** `{result.name}` expected `{result.expected_contains}`")
    return "\n".join(lines)
