# app.py

import gradio as gr

MODEL_ID = "DeepHat/DeepHat-V1-7B"
PROVIDER = "featherless-ai"

CSS = """
footer {
    display: none !important;
}

.gradio-container {
    max-width: 1400px !important;
    margin: auto !important;
}
"""

with gr.Blocks(
    title="DeepHat Inference Provider",
    fill_height=True,
    theme=gr.themes.Soft(),
    css=CSS,
) as demo:

    with gr.Sidebar():
        gr.Markdown(
            """
# Inference Provider

This Space showcases:

`DeepHat/DeepHat-V1-7B`

Served through:

`featherless-ai`

Sign in with your Hugging Face account to use the provider API.
"""
        )

        login_button = gr.LoginButton(
            value="Sign in with Hugging Face",
            variant="primary",
        )

        gr.Markdown(
            """
### Usage notes

- Hugging Face sign-in is required.
- Your token is handled through Gradio OAuth.
- Inference is routed through the selected provider.
"""
        )

    with gr.Column():
        gr.Markdown(
            """
# DeepHat V1 7B

Use the interface below to test prompts against the hosted model.
"""
        )

        gr.load(
            name=f"models/{MODEL_ID}",
            accept_token=login_button,
            provider=PROVIDER,
        )

if __name__ == "__main__":
    demo.launch()