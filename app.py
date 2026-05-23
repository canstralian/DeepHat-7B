import gradio as gr

with gr.Blocks(fill_height=True) as demo:
    with gr.Sidebar():
        gr.Markdown("# Inference Provider")
        gr.Markdown("This Space showcases the DeepHat/DeepHat-V1-7B model, served by the featherless-ai API. Sign in with your Hugging Face account to use this API.")
        button = gr.LoginButton("Sign in")
    gr.load("models/DeepHat/DeepHat-V1-7B", accept_token=button, provider="featherless-ai")
    
demo.launch()