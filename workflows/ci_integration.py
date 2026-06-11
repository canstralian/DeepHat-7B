#!/usr/bin/env python3
"""CI-oriented static security scan for changed files."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.tools.code_lint import lint_code


SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".go", ".rs", ".java", ".c", ".cpp", ".php", ".rb"}
DEFAULT_SCAN_ROOTS = [Path("app.py"), Path("api_client.py"), Path("cli.py"), Path("src"), Path("scripts"), Path("workflows")]


def changed_files() -> list[Path]:
    configured = os.getenv("CHANGED_FILES", "").split()
    if configured:
        return [Path(path) for path in configured]

    discovered: list[Path] = []
    for root in DEFAULT_SCAN_ROOTS:
        if root.is_file():
            discovered.append(root)
        elif root.is_dir():
            discovered.extend(root.rglob("*"))
    return [path for path in discovered if _is_scannable(path)]


def _is_scannable(path: Path) -> bool:
    return (
        path.is_file()
        and path.suffix in SUPPORTED_EXTENSIONS
        and not any(part in {".git", ".venv", "node_modules", "__pycache__"} for part in path.parts)
    )


def ci_scan() -> int:
    findings = []
    for path in changed_files():
        if not _is_scannable(path):
            continue
        code = path.read_text(encoding="utf-8", errors="replace")
        for finding in lint_code(code):
            findings.append({"file": str(path), **finding.__dict__})

    report_path = Path(os.getenv("SCAN_REPORT_PATH", "outputs/security_report.json"))
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(findings, indent=2), encoding="utf-8")

    high_findings = [finding for finding in findings if finding["severity"] == "high"]
    if high_findings:
        print(f"High severity findings detected: {len(high_findings)}")
        return 1
    print(f"Security scan completed. Findings: {len(findings)}")
    return 0


if __name__ == "__main__":
    sys.exit(ci_scan())
