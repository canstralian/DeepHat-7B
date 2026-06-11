"""Non-executing Python code checks for assistant-submitted snippets."""

from __future__ import annotations

import ast
from dataclasses import dataclass


@dataclass(frozen=True)
class CodeTestResult:
    syntax_ok: bool
    message: str
    function_count: int = 0
    test_function_count: int = 0


def analyze_python_code(code: str) -> CodeTestResult:
    """Parse Python code and report test-like structure without executing it."""

    if not code.strip():
        return CodeTestResult(syntax_ok=False, message="No Python code was provided.")

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return CodeTestResult(
            syntax_ok=False,
            message=f"SyntaxError on line {exc.lineno}: {exc.msg}",
        )

    functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    test_functions = [node for node in functions if node.name.startswith("test_")]
    return CodeTestResult(
        syntax_ok=True,
        message="Python syntax parsed successfully. Code was not executed.",
        function_count=len(functions),
        test_function_count=len(test_functions),
    )


def format_code_test_result(result: CodeTestResult) -> str:
    status = "passed" if result.syntax_ok else "failed"
    lines = [
        "### Code Test Summary",
        f"- Status: **{status}**",
        f"- Message: {result.message}",
    ]
    if result.syntax_ok:
        lines.extend(
            (
                f"- Functions discovered: {result.function_count}",
                f"- Test functions discovered: {result.test_function_count}",
            )
        )
    return "\n".join(lines)
