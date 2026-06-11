import os
from transformers import AutoTokenizer, AutoModelForCausalLM

def model_registry_lookup(prompt: str, context: List[Dict]) -> str:
    """Query DeepHat model with context."""
    tokenizer = AutoTokenizer.from_pretrained("DeepHat/DeepHat-V1-7B")
    model = AutoModelForCausalLM.from_pretrained("DeepHat/DeepHat-V1-7B")
    
    # Format prompt with context
    formatted_prompt = f"Context: {context}\n\nQuestion: {prompt}"
    inputs = tokenizer(formatted_prompt, return_tensors="pt")
    outputs = model.generate(**inputs, max_length=512)
    return tokenizer.decode(outputs[0])