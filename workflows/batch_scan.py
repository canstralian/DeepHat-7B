#!/usr/bin/env python3
"""Batch vulnerability analysis workflow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.agent import DeepHatAgent
from src.presets import SYSTEM_PRESETS
from src.tools.code_lint import lint_code
from src.utils import build_messages


SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".go", ".rs", ".java", ".c", ".cpp", ".php", ".rb"}


def scan_file_static(path: Path) -> dict[str, object]:
    code = path.read_text(encoding="utf-8", errors="replace")
    findings = lint_code(code)
    return {
        "file": str(path),
        "mode": "static",
        "status": "completed",
        "findings": [finding.__dict__ for finding in findings],
    }


def scan_file_with_model(agent: DeepHatAgent, path: Path) -> dict[str, object]:
    code = path.read_text(encoding="utf-8", errors="replace")[:12000]
    prompt = (
        "Perform an authorized secure code review. Identify vulnerabilities, affected "
        "locations, severity, evidence, and remediation.\n\n"
        f"File: {path}\n\n```{path.suffix.lstrip('.')}\n{code}\n```"
    )
    response = agent.generate(
        build_messages(SYSTEM_PRESETS["code_review"], [], prompt),
        temperature=0.2,
        max_new_tokens=2048,
    )
    return {
        "file": str(path),
        "mode": "model",
        "status": "completed",
        "analysis": response,
    }


def scan_directory(directory: Path, output_path: Path, use_model: bool, model_id: str) -> list[dict[str, object]]:
    agent = DeepHatAgent(model_id=model_id) if use_model else None
    results: list[dict[str, object]] = []

    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix not in SUPPORTED_EXTENSIONS:
            continue
        if any(part in {".git", ".venv", "node_modules", "__pycache__"} for part in path.parts):
            continue
        try:
            result = scan_file_with_model(agent, path) if agent else scan_file_static(path)
        except Exception as exc:
            result = {"file": str(path), "status": "error", "error": f"{type(exc).__name__}: {exc}"}
        results.append(result)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch security code scanner")
    parser.add_argument("--dir", "-d", type=Path, required=True, help="Directory to scan")
    parser.add_argument("--output", "-o", type=Path, default=Path("outputs/scan_results.json"))
    parser.add_argument("--model", default="DeepHat/DeepHat-V1-7B", help="Model ID for model-assisted scans")
    parser.add_argument("--use-model", action="store_true", help="Use DeepHat model inference instead of static checks")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = scan_directory(args.dir, args.output, args.use_model, args.model)
    errors = sum(1 for result in results if result.get("status") == "error")
    print(f"Scanned {len(results)} files. Errors: {errors}. Results: {args.output}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
