"""Simple policy text checks for common security controls."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyCheck:
    control: str
    status: str
    detail: str


CONTROL_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Authentication", ("auth", "login", "sso", "mfa", "identity")),
    ("Secrets Management", ("secret", "token", "key vault", "kms", "credential")),
    ("Logging and Monitoring", ("log", "monitor", "alert", "audit")),
    ("Data Protection", ("pii", "encrypt", "encryption", "retention", "privacy")),
    ("Change Control", ("review", "approval", "deployment", "rollback")),
)


def check_policy(text: str) -> list[PolicyCheck]:
    normalized = text.lower()
    checks: list[PolicyCheck] = []
    for control, keywords in CONTROL_KEYWORDS:
        matched = [keyword for keyword in keywords if keyword in normalized]
        if matched:
            checks.append(
                PolicyCheck(
                    control=control,
                    status="covered",
                    detail=f"Found related terms: {', '.join(matched)}.",
                )
            )
        else:
            checks.append(
                PolicyCheck(
                    control=control,
                    status="gap",
                    detail="No clear coverage found in the submitted text.",
                )
            )
    return checks


def format_policy_results(checks: list[PolicyCheck]) -> str:
    lines = ["### Policy Check"]
    for check in checks:
        label = "Covered" if check.status == "covered" else "Gap"
        lines.append(f"- **{label}: {check.control}** - {check.detail}")
    lines.append("")
    lines.append("This keyword check is a triage aid, not a compliance determination.")
    return "\n".join(lines)
