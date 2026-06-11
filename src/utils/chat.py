"""Chat formatting and export helpers."""

from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from src.utils.config import get_config


ChatMessage = dict[str, str]


def format_response(text: str) -> str:
    """Normalize model output for display."""

    return (text or "").strip()


def build_messages(system_prompt: str, history: list[ChatMessage], user_message: str) -> list[ChatMessage]:
    """Build model messages from Gradio message history."""

    messages: list[ChatMessage] = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})

    for message in history:
        role = message.get("role", "")
        content = message.get("content", "")
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})

    if user_message.strip():
        messages.append({"role": "user", "content": user_message.strip()})
    return messages


def export_chat(
    history: list[ChatMessage],
    format_type: str = "markdown",
    output_dir: Path | None = None,
) -> Path:
    """Export a chat history to Markdown, JSON, or HTML."""

    export_dir = output_dir or get_config().artifact_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    normalized_format = format_type.lower().strip()
    if normalized_format not in {"markdown", "json", "html"}:
        raise ValueError("format_type must be one of: markdown, json, html")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    extension = "md" if normalized_format == "markdown" else normalized_format
    path = export_dir / f"deephat-chat-{timestamp}.{extension}"

    if normalized_format == "json":
        path.write_text(json.dumps(history, indent=2), encoding="utf-8")
    elif normalized_format == "html":
        path.write_text(_render_html(history, timestamp), encoding="utf-8")
    else:
        path.write_text(_render_markdown(history, timestamp), encoding="utf-8")

    return path


def summarize_static_findings(text: str) -> tuple[str, list[str]]:
    """Extract rough severity signals from model or static scan output."""

    normalized = text.lower()
    severities: list[str] = []
    for severity in ("critical", "high", "medium", "low", "info"):
        if re.search(rf"\b{severity}\b", normalized):
            severities.append(severity)
    highest = severities[0] if severities else "none"
    return highest, severities


def _render_markdown(history: list[ChatMessage], timestamp: str) -> str:
    lines = [f"# DeepHat Conversation - {timestamp}", ""]
    for message in history:
        role = message.get("role", "message").title()
        content = message.get("content", "")
        lines.extend((f"## {role}", "", content, ""))
    return "\n".join(lines).rstrip() + "\n"


def _render_html(history: list[ChatMessage], timestamp: str) -> str:
    parts = [
        "<!doctype html>",
        "<html><head><meta charset=\"utf-8\">",
        "<style>body{font-family:system-ui;max-width:900px;margin:2rem auto;padding:0 1rem;}"
        "pre{white-space:pre-wrap;background:#f6f8fa;padding:1rem;border-radius:8px;}</style>",
        f"<title>DeepHat Conversation - {html.escape(timestamp)}</title></head><body>",
        f"<h1>DeepHat Conversation - {html.escape(timestamp)}</h1>",
    ]
    for message in history:
        role = html.escape(message.get("role", "message").title())
        content = html.escape(message.get("content", ""))
        parts.extend((f"<h2>{role}</h2>", f"<pre>{content}</pre>"))
    parts.append("</body></html>")
    return "\n".join(parts)


def messages_to_pairs(history: list[ChatMessage]) -> list[tuple[str, str]]:
    """Convert message dictionaries to legacy pair history."""

    pairs: list[tuple[str, str]] = []
    pending_user: str | None = None
    for message in history:
        if message.get("role") == "user":
            pending_user = message.get("content", "")
        elif message.get("role") == "assistant" and pending_user is not None:
            pairs.append((pending_user, message.get("content", "")))
            pending_user = None
    return pairs
