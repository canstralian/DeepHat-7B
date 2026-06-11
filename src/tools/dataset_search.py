"""Offline dataset search for common security analysis datasets."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetRecord:
    name: str
    use_case: str
    description: str
    risk_notes: str
    tags: tuple[str, ...]


DATASETS: tuple[DatasetRecord, ...] = (
    DatasetRecord(
        name="NVD CVE feeds",
        use_case="Vulnerability intelligence and CVE enrichment",
        description="Structured CVE metadata useful for triage, severity context, and affected product lookup.",
        risk_notes="Confirm current records against the live NVD source before operational use.",
        tags=("cve", "vulnerability", "nvd", "severity"),
    ),
    DatasetRecord(
        name="MalwareBazaar",
        use_case="Malware sample intelligence",
        description="Community malware sample metadata for hash-based investigation and family clustering.",
        risk_notes="Do not download or execute samples in this app; handle malware only in an isolated lab.",
        tags=("malware", "hash", "ioc", "sample"),
    ),
    DatasetRecord(
        name="CIC-IDS2017",
        use_case="Intrusion detection benchmarking",
        description="Network flow data covering benign traffic and common attack categories.",
        risk_notes="Benchmark results may not transfer to production networks without environment-specific validation.",
        tags=("ids", "network", "benchmark", "traffic"),
    ),
    DatasetRecord(
        name="PhishTank",
        use_case="Phishing URL analysis",
        description="Reported phishing URLs and verification status for URL classification experiments.",
        risk_notes="URLs can be dangerous to visit; defang or inspect through controlled tooling.",
        tags=("phishing", "url", "ioc"),
    ),
)


def search_datasets(query: str, limit: int = 3) -> list[DatasetRecord]:
    """Return matching local dataset records ordered by simple token overlap."""

    tokens = _query_tokens(query)
    if not tokens:
        return list(DATASETS[:limit])

    scored: list[tuple[int, DatasetRecord]] = []
    for dataset in DATASETS:
        haystack = " ".join(
            (
                dataset.name,
                dataset.use_case,
                dataset.description,
                " ".join(dataset.tags),
            )
        ).lower()
        score = sum(1 for token in tokens if token in haystack)
        if score:
            scored.append((score, dataset))

    scored.sort(key=lambda item: (-item[0], item[1].name))
    return [dataset for _, dataset in scored[:limit]]


def format_dataset_results(results: list[DatasetRecord]) -> str:
    if not results:
        return "No local dataset records matched. Try terms like `CVE`, `malware`, `IDS`, or `phishing`."

    lines = ["### Dataset Matches"]
    for record in results:
        lines.extend(
            (
                f"- **{record.name}**",
                f"  - Use case: {record.use_case}",
                f"  - Notes: {record.description}",
                f"  - Risk: {record.risk_notes}",
            )
        )
    return "\n".join(lines)


def _query_tokens(query: str) -> set[str]:
    return {token for token in query.lower().replace("-", " ").split() if len(token) > 2}
