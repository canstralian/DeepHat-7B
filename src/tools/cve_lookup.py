"""Small offline CVE lookup for deterministic demos and tests."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CveRecord:
    cve_id: str
    name: str
    severity: str
    summary: str
    remediation: str
    tags: tuple[str, ...]


CVE_RECORDS: tuple[CveRecord, ...] = (
    CveRecord(
        cve_id="CVE-2021-44228",
        name="Log4Shell",
        severity="Critical",
        summary="Remote code execution in Apache Log4j through crafted JNDI lookups.",
        remediation="Upgrade Log4j to a fixed release and remove vulnerable transitive dependencies.",
        tags=("log4j", "java", "rce", "jndi"),
    ),
    CveRecord(
        cve_id="CVE-2014-0160",
        name="Heartbleed",
        severity="High",
        summary="OpenSSL heartbeat memory disclosure affecting vulnerable TLS services.",
        remediation="Patch OpenSSL, rotate exposed keys, and reissue certificates.",
        tags=("openssl", "tls", "memory", "disclosure"),
    ),
    CveRecord(
        cve_id="CVE-2017-5638",
        name="Apache Struts Jakarta Multipart parser RCE",
        severity="Critical",
        summary="Remote command execution through crafted Content-Type headers.",
        remediation="Upgrade Apache Struts and inspect exposed systems for compromise.",
        tags=("struts", "apache", "rce", "header"),
    ),
    CveRecord(
        cve_id="CVE-2023-34362",
        name="MOVEit Transfer SQL injection",
        severity="Critical",
        summary="SQL injection in MOVEit Transfer enabling unauthorized access in affected deployments.",
        remediation="Apply vendor patches, rotate credentials, and review data access logs.",
        tags=("moveit", "sql", "injection", "file-transfer"),
    ),
)


def lookup_cves(query: str, limit: int = 5) -> list[CveRecord]:
    exact_ids = {match.upper() for match in re.findall(r"cve-\d{4}-\d{4,}", query, re.IGNORECASE)}
    if exact_ids:
        return [record for record in CVE_RECORDS if record.cve_id in exact_ids]

    tokens = _query_tokens(query)
    scored: list[tuple[int, CveRecord]] = []
    for record in CVE_RECORDS:
        haystack = " ".join(
            (
                record.cve_id,
                record.name,
                record.severity,
                record.summary,
                record.remediation,
                " ".join(record.tags),
            )
        ).lower()
        score = sum(1 for token in tokens if token in haystack)
        if score:
            scored.append((score, record))

    scored.sort(key=lambda item: (-item[0], item[1].cve_id))
    return [record for _, record in scored[:limit]]


def format_cve_results(results: list[CveRecord]) -> str:
    if not results:
        return (
            "No matching local CVE record found. This demo includes a small offline "
            "catalog only; verify operational findings against authoritative sources."
        )

    lines = ["### CVE Matches"]
    for record in results:
        lines.extend(
            (
                f"- **{record.cve_id}**: {record.name}",
                f"  - Severity: {record.severity}",
                f"  - Summary: {record.summary}",
                f"  - Remediation: {record.remediation}",
            )
        )
    return "\n".join(lines)


def _query_tokens(query: str) -> set[str]:
    return {token for token in query.lower().replace("-", " ").split() if len(token) > 2}
