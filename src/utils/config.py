"""Application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    app_title: str
    artifact_dir: Path


def get_config() -> AppConfig:
    project_root = Path(__file__).resolve().parents[2]
    artifact_dir = Path(os.getenv("SECURITY_ASSISTANT_ARTIFACT_DIR", project_root / "outputs" / "artifacts"))
    return AppConfig(
        app_title=os.getenv("SECURITY_ASSISTANT_TITLE", "Security Assistant"),
        artifact_dir=artifact_dir,
    )
