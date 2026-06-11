"""Local deterministic tools used by the security assistant.

This module also exposes legacy function names used by earlier Space entrypoints.
"""

from __future__ import annotations

from typing import Any

from src.tools.artifact_store import store_artifact
from src.tools.code_lint import lint_code
from src.tools.code_test import analyze_python_code
from src.tools.cve_lookup import format_cve_results, lookup_cves
from src.tools.dataset_search import search_datasets
from src.tools.eval_runner import run_evals
from src.tools.model_registry_lookup import model_registry_lookup
from src.tools.policy_check import check_policy


def dataset_search(query: str) -> list[dict[str, Any]]:
    return [
        {
            "name": record.name,
            "use_case": record.use_case,
            "description": record.description,
            "risk_notes": record.risk_notes,
            "tags": list(record.tags),
        }
        for record in search_datasets(query)
    ]


def cve_lookup(query: str) -> str:
    return format_cve_results(lookup_cves(query))


def code_lint(code: str) -> dict[str, Any]:
    findings = lint_code(code)
    return {
        "valid": not findings,
        "errors": [finding.__dict__ for finding in findings],
    }


def code_test(code: str) -> dict[str, Any]:
    result = analyze_python_code(code)
    return result.__dict__


def policy_check(text: str) -> dict[str, str | bool]:
    checks = check_policy(text)
    gaps = [check.control for check in checks if check.status == "gap"]
    return {
        "allowed": True,
        "reason": "Policy triage completed.",
        "gaps": ", ".join(gaps),
    }


def artifact_store(payload: Any) -> str:
    artifact = store_artifact(str(payload))
    return artifact.path


def eval_runner(prompt: str, expected: str) -> dict[str, Any]:
    return {
        "prompt": prompt,
        "expected": expected,
        "matched": expected.lower() in prompt.lower(),
    }
