import gradio as gr
from src.agent import SecurityAgent

# Initialize agent
agent = SecurityAgent()

def process_prompt(prompt):
    try:
        response = agent.generate(prompt)
        return response
    except Exception as e:
        return f"Error: {str(e)}"

# Create Gradio interface
with gr.Blocks() as demo:
    gr.Markdown("# Secure Code Assistant")
    input_prompt = gr.Textbox(label="Enter your request")
    output_response = gr.Textbox(label="Response")
    submit_btn = gr.Button("Submit")

    submit_btn.click(
        fn=process_prompt,
        inputs=input_prompt,
        outputs=output_response
    )

if __name__ == "__main__":
    demo.launch()