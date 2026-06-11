"""Publish the current checkout to a Hugging Face Space."""

from __future__ import annotations

import os

from huggingface_hub import HfApi


IGNORE_PATTERNS = [
    ".git/*",
    ".github/*",
    ".pytest_cache/*",
    ".venv/*",
    "__pycache__/*",
    "*.pyc",
    "outputs/*",
    "work/*",
]


def main() -> None:
    token = os.getenv("HF_TOKEN")
    if not token:
        raise SystemExit("HF_TOKEN is required to publish the Hugging Face Space.")

    space_id = os.getenv("HF_SPACE_ID", "S-Dreamer/DeepHat-7B")
    api = HfApi(token=token)
    api.upload_folder(
        repo_id=space_id,
        repo_type="space",
        folder_path=".",
        commit_message="chore: publish from github actions",
        ignore_patterns=IGNORE_PATTERNS,
    )


if __name__ == "__main__":
    main()
