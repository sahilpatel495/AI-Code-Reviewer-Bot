"""
Ultra-minimal Vercel serverless function - only FastAPI
"""

import json
from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "healthy", "message": "AI Code Reviewer Bot"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/webhook/github")
async def webhook(request: Request):
    try:
        body = await request.body()
        data = json.loads(body.decode())
        event = request.headers.get("X-GitHub-Event", "")
        
        if event == "pull_request":
            action = data.get("action")
            if action in ["opened", "synchronize"]:
                pr = data["pull_request"]
                print(f"PR #{pr['number']} {action}")
        
        return {"status": "success"}
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

handler = app