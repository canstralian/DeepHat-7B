"""Gradio entrypoint for the security assistant."""

from __future__ import annotations

import gradio as gr

from src.agent import SecurityAssistantAgent
from src.utils.config import get_config


TOOL_CHOICES = [
    "auto",
    "dataset_search",
    "model_registry_lookup",
    "cve_lookup",
    "code_lint",
    "code_test",
    "policy_check",
    "eval_runner",
]


def build_demo(agent: SecurityAssistantAgent | None = None) -> gr.Blocks:
    """Build the Gradio UI without launching it."""

    config = get_config()
    assistant = agent or SecurityAssistantAgent()

    with gr.Blocks(title=config.app_title) as demo:
        gr.Markdown(f"# {config.app_title}")
        gr.Markdown(
            "Ask for CVE context, dataset lookup, DeepHat model generation, "
            "code review, policy checks, or evaluation status."
        )

        with gr.Row():
            tool = gr.Dropdown(
                choices=TOOL_CHOICES,
                value="auto",
                label="Tool",
                info="Use auto routing or force a specific local tool.",
            )

        prompt = gr.Textbox(
            label="Request",
            lines=8,
            placeholder=(
                "Examples: CVE-2021-44228, lint this Python snippet, "
                "check this deployment policy, search malware datasets"
            ),
        )
        output = gr.Markdown(label="Assistant response")

        with gr.Row():
            submit = gr.Button("Analyze", variant="primary")
            clear = gr.ClearButton([prompt, output])

        submit.click(
            fn=assistant.respond,
            inputs=[prompt, tool],
            outputs=output,
            api_name="analyze",
        )
        prompt.submit(
            fn=assistant.respond,
            inputs=[prompt, tool],
            outputs=output,
            api_name=False,
        )

    return demo


if __name__ == "__main__":
    build_demo().launch()
