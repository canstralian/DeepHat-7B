"""Safe local artifact persistence for assistant outputs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from src.utils.config import get_config


@dataclass(frozen=True)
class StoredArtifact:
    name: str
    path: str


def store_artifact(content: str, title: str = "security-assistant-note", base_dir: Path | None = None) -> StoredArtifact:
    """Store Markdown content under the configured artifact directory."""

    output_dir = base_dir or get_config().artifact_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = _slugify(title)
    filename = f"{timestamp}-{slug}.md"
    path = output_dir / filename
    path.write_text(content.strip() + "\n", encoding="utf-8")
    return StoredArtifact(name=filename, path=str(path))


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "artifact"
