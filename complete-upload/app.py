"""
AI Code Reviewer Bot - FastAPI Application

This is the main FastAPI application that handles GitHub webhooks,
manages authentication, and coordinates the code review process.
"""

import asyncio
import hashlib
import hmac
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

import structlog
from fastapi import FastAPI, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config.settings import settings
from services.github_service import GitHubService
from services.ai_service import AIService
from services.analyzer_service import AnalyzerService
from db.models import ReviewSession, ReviewComment
from db.session import get_db_session
from jobs.review_task import process_pr_review

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# FastAPI app instance
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered code review bot for GitHub Pull Requests",
    debug=settings.debug
)

# Service instances
github_service = GitHubService()
ai_service = AIService()
analyzer_service = AnalyzerService()


class WebhookPayload(BaseModel):
    """GitHub webhook payload model."""
    action: str
    pull_request: Dict[str, Any]
    repository: Dict[str, Any]
    installation: Optional[Dict[str, Any]] = None


class ReviewRequest(BaseModel):
    """Manual review request model."""
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    pull_number: int = Field(..., description="Pull request number")
    focus_area: Optional[str] = Field(None, description="Specific area to focus on (security, performance, etc.)")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests."""
    start_time = datetime.now(timezone.utc)
    
    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    response = await call_next(request)
    
    # Log response
    process_time = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info(
        "Request completed",
        status_code=response.status_code,
        process_time=process_time
    )
    
    return response


def verify_github_signature(payload: bytes, signature: str) -> bool:
    """
    Verify GitHub webhook signature using HMAC-SHA256.
    
    Args:
        payload: Raw request body
        signature: GitHub signature header
        
    Returns:
        True if signature is valid, False otherwise
    """
    if not signature.startswith("sha256="):
        return False
    
    expected_signature = hmac.new(
        settings.github_webhook_secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    received_signature = signature[7:]  # Remove "sha256=" prefix
    
    return hmac.compare_digest(expected_signature, received_signature)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    try:
        # Check database connection
        db_session = next(get_db_session())
        db_session.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        db_status = "unhealthy"
    
    try:
        # Check Redis connection
        import redis
        r = redis.from_url(settings.redis_url)
        r.ping()
        redis_status = "healthy"
    except Exception as e:
        logger.error("Redis health check failed", error=str(e))
        redis_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded",
        "components": {
            "database": db_status,
            "redis": redis_status,
            "github_api": "healthy",  # Will be tested when needed
            "gemini_api": "healthy"   # Will be tested when needed
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/webhook/github")
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_event: str = None,
    x_github_delivery: str = None,
    x_hub_signature_256: str = None
):
    """
    Handle GitHub webhook events.
    
    This endpoint processes GitHub webhook events, particularly pull request events,
    and triggers the code review process.
    """
    try:
        # Get raw payload
        payload = await request.body()
        
        # Verify signature
        if not verify_github_signature(payload, x_hub_signature_256):
            logger.warning("Invalid GitHub webhook signature", delivery_id=x_github_delivery)
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse payload
        try:
            webhook_data = json.loads(payload.decode())
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON payload", error=str(e), delivery_id=x_github_delivery)
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # Log webhook event
        logger.info(
            "GitHub webhook received",
            event=x_github_event,
            delivery_id=x_github_delivery,
            action=webhook_data.get("action"),
            repository=webhook_data.get("repository", {}).get("full_name"),
            pull_number=webhook_data.get("pull_request", {}).get("number")
        )
        
        # Process pull request events
        if x_github_event == "pull_request":
            action = webhook_data.get("action")
            if action in ["opened", "synchronize", "ready_for_review"]:
                pr_data = webhook_data.get("pull_request", {})
                repo_data = webhook_data.get("repository", {})
                installation_data = webhook_data.get("installation", {})
                
                # Validate required data
                if not all([pr_data, repo_data, installation_data]):
                    logger.error("Missing required webhook data", delivery_id=x_github_delivery)
                    raise HTTPException(status_code=400, detail="Missing required data")
                
                # Queue review task
                background_tasks.add_task(
                    process_pr_review,
                    owner=repo_data["owner"]["login"],
                    repo=repo_data["name"],
                    pull_number=pr_data["number"],
                    installation_id=installation_data["id"],
                    action=action
                )
                
                logger.info(
                    "Review task queued",
                    owner=repo_data["owner"]["login"],
                    repo=repo_data["name"],
                    pull_number=pr_data["number"],
                    action=action
                )
        
        return {"status": "accepted", "delivery_id": x_github_delivery}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Webhook processing failed", error=str(e), delivery_id=x_github_delivery)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/review")
async def trigger_review(
    review_request: ReviewRequest,
    background_tasks: BackgroundTasks
):
    """
    Manually trigger a code review for a specific pull request.
    
    This endpoint allows manual triggering of code reviews, useful for
    testing or re-reviewing PRs after changes.
    """
    try:
        # Get installation ID for the repository
        installation_id = await github_service.get_installation_id(
            review_request.owner,
            review_request.repo
        )
        
        if not installation_id:
            raise HTTPException(
                status_code=404,
                detail=f"GitHub App not installed on {review_request.owner}/{review_request.repo}"
            )
        
        # Queue review task
        background_tasks.add_task(
            process_pr_review,
            owner=review_request.owner,
            repo=review_request.repo,
            pull_number=review_request.pull_number,
            installation_id=installation_id,
            action="manual_trigger",
            focus_area=review_request.focus_area
        )
        
        logger.info(
            "Manual review triggered",
            owner=review_request.owner,
            repo=review_request.repo,
            pull_number=review_request.pull_number,
            focus_area=review_request.focus_area
        )
        
        return {
            "status": "accepted",
            "message": f"Review queued for {review_request.owner}/{review_request.repo}#{review_request.pull_number}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Manual review trigger failed", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/reviews/{owner}/{repo}/{pull_number}")
async def get_review_status(
    owner: str,
    repo: str,
    pull_number: int
):
    """
    Get the status of a code review for a specific pull request.
    
    Returns information about the review session, including comments
    posted and overall status.
    """
    try:
        db_session = next(get_db_session())
        
        # Get review session
        review_session = db_session.query(ReviewSession).filter(
            ReviewSession.owner == owner,
            ReviewSession.repo == repo,
            ReviewSession.pull_number == pull_number
        ).order_by(ReviewSession.created_at.desc()).first()
        
        if not review_session:
            raise HTTPException(status_code=404, detail="Review session not found")
        
        # Get comments
        comments = db_session.query(ReviewComment).filter(
            ReviewComment.review_session_id == review_session.id
        ).all()
        
        return {
            "review_session": {
                "id": review_session.id,
                "status": review_session.status,
                "created_at": review_session.created_at.isoformat(),
                "completed_at": review_session.completed_at.isoformat() if review_session.completed_at else None,
                "total_comments": len(comments),
                "risk_level": review_session.risk_level,
                "approval_recommendation": review_session.approval_recommendation
            },
            "comments": [
                {
                    "id": comment.id,
                    "path": comment.file_path,
                    "start_line": comment.start_line,
                    "end_line": comment.end_line,
                    "severity": comment.severity,
                    "category": comment.category,
                    "comment": comment.comment,
                    "created_at": comment.created_at.isoformat()
                }
                for comment in comments
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get review status", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/stats")
async def get_stats():
    """
    Get application statistics.
    
    Returns metrics about reviews performed, success rates, and other
    operational statistics.
    """
    try:
        db_session = next(get_db_session())
        
        # Get basic stats
        total_reviews = db_session.query(ReviewSession).count()
        completed_reviews = db_session.query(ReviewSession).filter(
            ReviewSession.status == "completed"
        ).count()
        
        # Get recent activity
        recent_reviews = db_session.query(ReviewSession).filter(
            ReviewSession.created_at >= datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        ).count()
        
        return {
            "total_reviews": total_reviews,
            "completed_reviews": completed_reviews,
            "success_rate": (completed_reviews / total_reviews * 100) if total_reviews > 0 else 0,
            "reviews_today": recent_reviews,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )