"""
Ultra-minimal Vercel serverless function for AI Code Reviewer Bot
"""

import os
import json
import hmac
import hashlib
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# FastAPI app instance
app = FastAPI(title="AI Code Reviewer Bot", version="1.0.0")

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

@app.get("/")
async def root():
    """Root endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.post("/webhook/github")
async def github_webhook(request: Request):
    """GitHub webhook handler"""
    try:
        body = await request.body()
        payload = json.loads(body.decode())
        event_type = request.headers.get("X-GitHub-Event", "")
        
        # Basic webhook processing
        if event_type == "pull_request":
            action = payload.get("action")
            if action in ["opened", "synchronize", "ready_for_review"]:
                pr = payload["pull_request"]
                repo = payload["repository"]
                print(f"PR #{pr['number']} {action} in {repo['full_name']}")
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Export for Vercel
handler = app