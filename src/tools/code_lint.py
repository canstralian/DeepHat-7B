"""Static security lint checks that never execute user code."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Pattern


@dataclass(frozen=True)
class LintRule:
    rule_id: str
    severity: str
    pattern: Pattern[str]
    message: str


@dataclass(frozen=True)
class LintFinding:
    rule_id: str
    severity: str
    line_number: int
    message: str
    evidence: str


RULES: tuple[LintRule, ...] = (
    LintRule(
        rule_id="hardcoded-secret",
        severity="high",
        pattern=re.compile(
            r"(?i)\b(api[_-]?key|secret|token|password)\b\s*[:=]\s*['\"][^'\"]{8,}['\"]"
        ),
        message="Potential hardcoded credential or secret.",
    ),
    LintRule(
        rule_id="shell-true",
        severity="high",
        pattern=re.compile(r"\bshell\s*=\s*True\b"),
        message="Avoid shell=True unless input is fully controlled and justified.",
    ),
    LintRule(
        rule_id="unsafe-eval",
        severity="high",
        pattern=re.compile(r"\b(eval|exec)\s*\("),
        message="Dynamic code execution can lead to remote code execution.",
    ),
    LintRule(
        rule_id="tls-verify-disabled",
        severity="medium",
        pattern=re.compile(r"\bverify\s*=\s*False\b"),
        message="TLS certificate verification is disabled.",
    ),
    LintRule(
        rule_id="pickle-load",
        severity="medium",
        pattern=re.compile(r"\bpickle\.loads?\s*\("),
        message="Pickle can execute code when loading untrusted data.",
    ),
    LintRule(
        rule_id="yaml-load",
        severity="medium",
        pattern=re.compile(r"\byaml\.load\s*\("),
        message="Use yaml.safe_load for untrusted YAML input.",
    ),
)


def lint_code(code: str) -> list[LintFinding]:
    if not code.strip():
        return []

    findings: list[LintFinding] = []
    for line_number, line in enumerate(code.splitlines(), start=1):
        for rule in RULES:
            if rule.pattern.search(line):
                findings.append(
                    LintFinding(
                        rule_id=rule.rule_id,
                        severity=rule.severity,
                        line_number=line_number,
                        message=rule.message,
                        evidence=line.strip(),
                    )
                )
    return findings


def format_lint_results(findings: list[LintFinding]) -> str:
    if not findings:
        return "No findings from the local static rules. This is not a complete security audit."

    severity_order = {"high": 0, "medium": 1, "low": 2}
    sorted_findings = sorted(
        findings,
        key=lambda finding: (severity_order.get(finding.severity, 99), finding.line_number),
    )
    lines = ["### Static Security Findings"]
    for finding in sorted_findings:
        lines.extend(
            (
                f"- **{finding.severity.upper()}** `{finding.rule_id}` on line {finding.line_number}",
                f"  - {finding.message}",
                f"  - Evidence: `{finding.evidence}`",
            )
        )
    return "\n".join(lines)
