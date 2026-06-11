import gradio as gr
import json
import time
from src.agent import SecurityAgent

# Initialize agent
agent = SecurityAgent()

def process_prompt(prompt):
    start_time = time.time()
    try:
        response = agent.generate(prompt)
        duration = time.time() - start_time
        
        return {
            "response": response,
            "metadata": {
                "processing_time_ms": round(duration * 1000, 2),
                "timestamp": int(start_time)
            }
        }
    except Exception as e:
        return {"error": str(e)}

# Create Gradio interface
with gr.Blocks(title="Security Assistant") as demo:
    gr.Markdown("# Secure Code Assistant")
    
    with gr.Row():
        with gr.Column(scale=1):
            prompt_input = gr.Textbox(
                label="Prompt",
                placeholder="Enter your security question...",
                lines=5
            )
            submit_btn = gr.Button("Generate")
            
        with gr.Column(scale=2):
            response_output = gr.JSON(label="Response")
    
    submit_btn.click(
        fn=process_prompt,
        inputs=prompt_input,
        outputs=response_output
    )

if __name__ == "__main__":
    demo.launch()