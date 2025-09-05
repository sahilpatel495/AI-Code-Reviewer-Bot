"""
Vercel serverless function entry point for AI Code Reviewer Bot
Optimized for Vercel deployment without database dependencies
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
from pydantic import BaseModel

# Configure basic logging for Vercel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app instance
app = FastAPI(
    title="AI Code Reviewer Bot",
    description="AI-powered code reviewer using Gemini 2.5 Pro",
    version="1.0.0"
)

# Pydantic models
class WebhookPayload(BaseModel):
    action: str
    pull_request: Dict[str, Any]
    repository: Dict[str, Any]

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str

# Environment variables with defaults
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_APP_ID = os.getenv("GITHUB_APP_ID")
GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0"
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0"
    )

@app.post("/webhook/github")
async def github_webhook(request: Request):
    """GitHub webhook handler"""
    try:
        # Get the raw body
        body = await request.body()
        
        # Verify webhook signature if secret is configured
        if GITHUB_WEBHOOK_SECRET:
            signature = request.headers.get("X-Hub-Signature-256", "")
            if not _verify_webhook_signature(body, signature, GITHUB_WEBHOOK_SECRET):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse the payload
        payload = json.loads(body.decode())
        event_type = request.headers.get("X-GitHub-Event", "")
        
        logger.info(f"Received {event_type} event", action=payload.get("action"))
        
        # Handle pull request events
        if event_type == "pull_request":
            action = payload.get("action")
            if action in ["opened", "synchronize", "ready_for_review"]:
                await _handle_pull_request(payload)
        
        return JSONResponse(content={"status": "success"})
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def _handle_pull_request(payload: Dict[str, Any]):
    """Handle pull request events"""
    try:
        pr = payload["pull_request"]
        repo = payload["repository"]
        
        logger.info(f"Processing PR #{pr['number']} in {repo['full_name']}")
        
        # For now, just log the event
        # In a full implementation, this would trigger the AI review
        logger.info("PR review would be triggered here")
        
    except Exception as e:
        logger.error(f"Error handling PR: {str(e)}")

def _verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify GitHub webhook signature"""
    import hmac
    import hashlib
    
    if not signature.startswith("sha256="):
        return False
    
    expected_signature = "sha256=" + hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

# Export the app for Vercel
handler = app