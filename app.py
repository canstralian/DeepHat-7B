"""Enhanced Gradio Space entrypoint for DeepHat security assistance."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import gradio as gr

from src.agent import DeepHatAgent, SecurityAssistantAgent
from src.presets import EXAMPLE_PROMPTS, SYSTEM_PRESETS
from src.utils import build_messages, export_chat, format_response
from src.utils.config import get_config


MODEL_ID = os.getenv("MODEL_ID", "DeepHat/DeepHat-V1-7B")
DEVICE = os.getenv("DEVICE", "auto")
USE_4BIT = os.getenv("USE_4BIT", "false").lower() == "true"

MODEL_AGENT = DeepHatAgent(model_id=MODEL_ID, device=DEVICE, load_in_4bit=USE_4BIT)
TRIAGE_AGENT = SecurityAssistantAgent()

PRESET_CHOICES = list(SYSTEM_PRESETS)
EXAMPLE_CHOICES = [
    ("Pentest reconnaissance", "pentest_recon"),
    ("Code security review", "code_review"),
    ("Defensive hardening", "defensive_config"),
    ("Malware analysis", "malware_analysis"),
    ("CVE explainer", "cve_explain"),
]


def chat_stream(
    message: str,
    history: list[dict[str, str]] | None,
    system_prompt: str,
    preset_name: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
) -> Any:
    """Stream chat responses into a Gradio messages-style Chatbot."""

    current_history = list(history or [])
    normalized_message = (message or "").strip()
    if not normalized_message:
        yield current_history
        return

    selected_prompt = system_prompt.strip() or SYSTEM_PRESETS.get(preset_name, SYSTEM_PRESETS["default"])
    model_messages = build_messages(selected_prompt, current_history, normalized_message)

    current_history.append({"role": "user", "content": normalized_message})
    current_history.append({"role": "assistant", "content": ""})
    yield current_history

    partial_response = ""
    try:
        for chunk in MODEL_AGENT.generate_stream(
            messages=model_messages,
            temperature=temperature,
            max_new_tokens=int(max_tokens),
            top_p=top_p,
        ):
            partial_response += chunk
            current_history[-1]["content"] = format_response(partial_response)
            yield current_history
    except Exception as exc:
        fallback = TRIAGE_AGENT.respond(normalized_message, "auto")
        current_history[-1]["content"] = (
            "Model generation is unavailable in this runtime.\n\n"
            f"Reason: `{type(exc).__name__}: {exc}`\n\n"
            "Local triage fallback:\n\n"
            f"{fallback}"
        )
        yield current_history


def chat_once(
    message: str,
    preset_name: str = "default",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    top_p: float = 0.9,
) -> str:
    """API-friendly single-turn endpoint."""

    system_prompt = SYSTEM_PRESETS.get(preset_name, SYSTEM_PRESETS["default"])
    messages = build_messages(system_prompt, [], message)
    try:
        return MODEL_AGENT.generate(
            messages=messages,
            temperature=temperature,
            max_new_tokens=int(max_tokens),
            top_p=top_p,
        )
    except Exception as exc:
        fallback = TRIAGE_AGENT.respond(message, "auto")
        return (
            "Model generation is unavailable in this runtime.\n\n"
            f"Reason: `{type(exc).__name__}: {exc}`\n\n"
            "Local triage fallback:\n\n"
            f"{fallback}"
        )


def clear_chat() -> tuple[str, list[dict[str, str]]]:
    return "", []


def load_example(example_name: str | None) -> str:
    if not example_name:
        return ""
    return EXAMPLE_PROMPTS.get(example_name, "")


def update_system_prompt(preset_name: str) -> str:
    return SYSTEM_PRESETS.get(preset_name, SYSTEM_PRESETS["default"])


def export_conversation(history: list[dict[str, str]] | None, format_type: str) -> tuple[str, str | None]:
    if not history:
        return "No conversation to export.", None
    try:
        path = export_chat(history, format_type)
    except ValueError as exc:
        return str(exc), None
    return f"Exported {format_type} conversation to {Path(path).name}.", str(path)


def build_demo() -> gr.Blocks:
    """Build the Gradio UI without launching it."""

    config = get_config()

    with gr.Blocks(title=config.app_title) as demo:
        gr.Markdown(
            """
# DeepHat 7B Security Assistant

Cybersecurity-focused chat, local triage tools, and workflow helpers. Use only on systems you own or are authorized to assess.
            """.strip()
        )

        with gr.Row():
            with gr.Column(scale=1, min_width=300):
                gr.Markdown("### Configuration")
                preset_dropdown = gr.Dropdown(
                    choices=PRESET_CHOICES,
                    value="default",
                    label="Agent Mode",
                    filterable=False,
                )
                system_prompt = gr.Textbox(
                    value=SYSTEM_PRESETS["default"],
                    label="System Prompt",
                    lines=7,
                    interactive=True,
                )
                preset_dropdown.change(
                    fn=update_system_prompt,
                    inputs=preset_dropdown,
                    outputs=system_prompt,
                    api_name=False,
                )

                gr.Markdown("### Generation")
                temperature = gr.Slider(0.0, 1.5, value=0.7, step=0.05, label="Temperature")
                max_tokens = gr.Slider(64, 8192, value=2048, step=64, label="Max New Tokens")
                top_p = gr.Slider(0.1, 1.0, value=0.9, step=0.05, label="Top-p")

                gr.Markdown("### Export")
                export_format = gr.Dropdown(
                    ["markdown", "json", "html"],
                    value="markdown",
                    label="Format",
                    filterable=False,
                )
                export_btn = gr.Button("Export Conversation", variant="secondary")
                export_status = gr.Textbox(label="Export Status", interactive=False)
                export_file = gr.File(label="Download Export", interactive=False)

            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=560,
                    type="messages",
                    buttons=["copy"],
                )
                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="Ask DeepHat about authorized cybersecurity work...",
                        show_label=False,
                        lines=3,
                        scale=8,
                    )
                    submit_btn = gr.Button("Send", variant="primary", scale=1)
                    clear_btn = gr.Button("Clear", variant="secondary", scale=1)

                example_dropdown = gr.Dropdown(
                    choices=EXAMPLE_CHOICES,
                    value=None,
                    label="Quick Examples",
                    filterable=False,
                )
                example_dropdown.change(
                    fn=load_example,
                    inputs=example_dropdown,
                    outputs=msg_input,
                    api_name=False,
                )

        chat_inputs = [msg_input, chatbot, system_prompt, preset_dropdown, temperature, max_tokens, top_p]
        submit_btn.click(
            fn=chat_stream,
            inputs=chat_inputs,
            outputs=chatbot,
            queue=True,
            api_name="chat",
        ).then(lambda: "", None, msg_input, api_name=False)

        msg_input.submit(
            fn=chat_stream,
            inputs=chat_inputs,
            outputs=chatbot,
            queue=True,
            api_name=False,
        ).then(lambda: "", None, msg_input, api_name=False)

        clear_btn.click(fn=clear_chat, outputs=[msg_input, chatbot], api_name=False)
        export_btn.click(
            fn=export_conversation,
            inputs=[chatbot, export_format],
            outputs=[export_status, export_file],
            api_name="export",
        )

        gr.Markdown(
            "DeepHat may generate inaccurate output. Verify findings against source evidence, "
            "current advisories, and your authorization scope before acting."
        )

    return demo


if __name__ == "__main__":
    build_demo().queue(max_size=20).launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        share=False,
    )
