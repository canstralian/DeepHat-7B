from fastapi import FastAPI, HTTPException
import uvicorn
from src.agent import SecurityAgent

app = FastAPI(title="Security Assistant")
agent = SecurityAgent()

@app.get("/")
async def health():
    return {"status": "healthy"}

@app.post("/generate")
async def generate(prompt: str):
    try:
        response = agent.generate(prompt)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)