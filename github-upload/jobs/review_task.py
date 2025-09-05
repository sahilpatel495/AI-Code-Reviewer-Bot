"""
Celery Task for Processing PR Reviews

This module contains the Celery task that processes pull request reviews
in the background, including fetching diffs, running static analysis,
and generating AI reviews.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

import structlog
from celery import Celery
from celery.exceptions import Retry

from config.settings import settings
from services.github_service import GitHubService
from services.ai_service import AIService
from services.analyzer_service import AnalyzerService
from db.models import ReviewSession, ReviewComment, WebhookEvent
from db.session import get_db_session

logger = structlog.get_logger(__name__)

# Initialize Celery
celery_app = Celery(
    "ai_reviewer",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=settings.review_timeout_seconds,
    task_soft_time_limit=settings.review_timeout_seconds - 30,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=True,
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    result_expires=3600,  # 1 hour
    task_routes={
        "jobs.review_task.process_pr_review": {"queue": "reviews"},
        "jobs.review_task.cleanup_old_sessions": {"queue": "maintenance"},
    }
)

# Initialize services
github_service = GitHubService()
ai_service = AIService()
analyzer_service = AnalyzerService()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_pr_review(self, owner: str, repo: str, pull_number: int, installation_id: str, action: str, focus_area: Optional[str] = None):
    """
    Process a pull request review.
    
    This is the main Celery task that orchestrates the entire review process:
    1. Fetch PR data and diff
    2. Run static analysis
    3. Generate AI review
    4. Post comments to GitHub
    5. Update PR status
    
    Args:
        owner: Repository owner
        repo: Repository name
        pull_number: Pull request number
        installation_id: GitHub App installation ID
        action: Webhook action that triggered the review
        focus_area: Optional focus area for the review
    """
    review_session_id = None
    start_time = time.time()
    
    try:
        logger.info(
            "Starting PR review task",
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            installation_id=installation_id,
            action=action,
            focus_area=focus_area,
            task_id=self.request.id
        )
        
        # Create review session
        with get_db_session() as db_session:
            review_session = ReviewSession(
                owner=owner,
                repo=repo,
                pull_number=pull_number,
                installation_id=installation_id,
                status="in_progress",
                started_at=datetime.now(timezone.utc)
            )
            db_session.add(review_session)
            db_session.commit()
            review_session_id = review_session.id
            
            logger.info("Review session created", session_id=review_session_id)
        
        # Run the review process
        asyncio.run(_run_review_process(
            review_session_id=review_session_id,
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            installation_id=installation_id,
            action=action,
            focus_area=focus_area
        ))
        
        # Update review session as completed
        duration = int(time.time() - start_time)
        with get_db_session() as db_session:
            review_session = db_session.query(ReviewSession).filter(
                ReviewSession.id == review_session_id
            ).first()
            
            if review_session:
                review_session.status = "completed"
                review_session.completed_at = datetime.now(timezone.utc)
                review_session.review_duration_seconds = duration
                db_session.commit()
                
                logger.info(
                    "Review session completed",
                    session_id=review_session_id,
                    duration=duration
                )
        
        return {
            "status": "success",
            "review_session_id": review_session_id,
            "duration": duration
        }
        
    except Exception as e:
        logger.error(
            "PR review task failed",
            error=str(e),
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            review_session_id=review_session_id,
            task_id=self.request.id
        )
        
        # Update review session as failed
        if review_session_id:
            with get_db_session() as db_session:
                review_session = db_session.query(ReviewSession).filter(
                    ReviewSession.id == review_session_id
                ).first()
                
                if review_session:
                    review_session.status = "failed"
                    review_session.error_message = str(e)
                    review_session.error_details = {
                        "task_id": self.request.id,
                        "retry_count": self.request.retries,
                        "action": action,
                        "focus_area": focus_area
                    }
                    db_session.commit()
        
        # Retry if we haven't exceeded max retries
        if self.request.retries < self.max_retries:
            logger.info(
                "Retrying PR review task",
                retry_count=self.request.retries + 1,
                max_retries=self.max_retries,
                task_id=self.request.id
            )
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        # If we've exceeded max retries, mark as permanently failed
        raise e


async def _run_review_process(review_session_id: int, owner: str, repo: str, pull_number: int, installation_id: str, action: str, focus_area: Optional[str] = None):
    """Run the actual review process."""
    try:
        # Step 1: Fetch PR data and diff
        logger.info("Fetching PR data", session_id=review_session_id)
        
        pr_data = await github_service.get_pull_request(owner, repo, pull_number, installation_id)
        pr_diff = await github_service.get_pull_request_diff(owner, repo, pull_number, installation_id)
        pr_files = await github_service.get_pull_request_files(owner, repo, pull_number, installation_id)
        
        # Get repository languages
        languages = await github_service.get_repository_languages(owner, repo, installation_id)
        
        # Step 2: Extract file contents for analysis
        file_contents = {}
        file_paths = []
        
        for file_info in pr_files:
            if file_info["status"] in ["added", "modified"]:
                file_path = file_info["filename"]
                file_paths.append(file_path)
                
                # Get file content
                try:
                    content = await github_service.get_file_content(
                        owner, repo, file_path, pr_data["head"]["sha"], installation_id
                    )
                    file_contents[file_path] = content
                except Exception as e:
                    logger.warning(
                        "Failed to get file content",
                        file_path=file_path,
                        error=str(e),
                        session_id=review_session_id
                    )
        
        # Step 3: Run static analysis
        logger.info("Running static analysis", session_id=review_session_id)
        
        static_analysis_results = await analyzer_service.analyze_files(file_paths, file_contents)
        
        # Step 4: Generate AI review
        logger.info("Generating AI review", session_id=review_session_id)
        
        # Format static analysis results for AI
        analysis_summary = _format_static_analysis_results(static_analysis_results)
        
        # Generate review using AI
        review_data = await ai_service.review_code_changes_batch(
            file_paths=file_paths,
            languages=languages,
            static_analysis_results=analysis_summary,
            code_diff=pr_diff,
            max_comments=settings.max_comments_per_pr
        )
        
        # Step 5: Save review comments to database
        logger.info("Saving review comments", session_id=review_session_id)
        
        with get_db_session() as db_session:
            review_session = db_session.query(ReviewSession).filter(
                ReviewSession.id == review_session_id
            ).first()
            
            if review_session:
                # Update session with review results
                review_session.risk_level = review_data["risk"]
                review_session.approval_recommendation = review_data["approval_recommendation"]
                review_session.breaking_changes = review_data["breaking_changes"]
                review_session.files_changed = file_paths
                review_session.languages_detected = languages
                review_session.lines_added = sum(f.get("additions", 0) for f in pr_files)
                review_session.lines_removed = sum(f.get("deletions", 0) for f in pr_files)
                review_session.ai_model_used = "gemini-2.0-flash-exp"  # This should come from AI service
                
                # Save comments
                for comment_data in review_data["inline_comments"]:
                    comment = ReviewComment(
                        review_session_id=review_session_id,
                        file_path=comment_data["path"],
                        start_line=comment_data["start_line"],
                        end_line=comment_data["end_line"],
                        severity=comment_data["severity"],
                        category=comment_data["category"],
                        comment=comment_data["comment"]
                    )
                    db_session.add(comment)
                
                db_session.commit()
        
        # Step 6: Post comments to GitHub
        logger.info("Posting comments to GitHub", session_id=review_session_id)
        
        await _post_comments_to_github(
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            installation_id=installation_id,
            review_data=review_data,
            review_session_id=review_session_id
        )
        
        # Step 7: Create/update check run
        logger.info("Creating check run", session_id=review_session_id)
        
        await _create_check_run(
            owner=owner,
            repo=repo,
            pull_number=pull_number,
            installation_id=installation_id,
            review_data=review_data,
            static_analysis_results=static_analysis_results
        )
        
        logger.info("Review process completed successfully", session_id=review_session_id)
        
    except Exception as e:
        logger.error("Review process failed", error=str(e), session_id=review_session_id)
        raise


def _format_static_analysis_results(analysis_results: Dict[str, Any]) -> str:
    """Format static analysis results for AI consumption."""
    if not analysis_results or "summary" not in analysis_results:
        return "No static analysis results available."
    
    summary = analysis_results["summary"]
    formatted = f"Static Analysis Summary: {summary['message']}\n"
    formatted += f"Total Issues: {summary['total_issues']}\n"
    formatted += f"Files Analyzed: {summary['total_files']}\n"
    
    if summary["issues_by_severity"]:
        formatted += "Issues by Severity:\n"
        for severity, count in summary["issues_by_severity"].items():
            if count > 0:
                formatted += f"  - {severity}: {count}\n"
    
    # Add file-specific issues
    if "files" in analysis_results:
        formatted += "\nFile-specific Issues:\n"
        for file_path, file_results in analysis_results["files"].items():
            if file_results.get("issues"):
                formatted += f"\n{file_path}:\n"
                for issue in file_results["issues"][:5]:  # Limit to 5 issues per file
                    formatted += f"  - {issue['severity']}: {issue['message']} (line {issue['line']})\n"
    
    return formatted


async def _post_comments_to_github(owner: str, repo: str, pull_number: int, installation_id: str, review_data: Dict[str, Any], review_session_id: int):
    """Post review comments to GitHub."""
    try:
        # Group comments by file
        comments_by_file = {}
        for comment_data in review_data["inline_comments"]:
            file_path = comment_data["path"]
            if file_path not in comments_by_file:
                comments_by_file[file_path] = []
            comments_by_file[file_path].append(comment_data)
        
        # Post comments for each file
        for file_path, comments in comments_by_file.items():
            if not comments:
                continue
            
            # Create review comment
            review_comment = {
                "body": f"## AI Code Review - {file_path}\n\n" + "\n\n".join([
                    f"**{c['severity'].upper()}** ({c['category']}): {c['comment']}"
                    for c in comments
                ]),
                "event": "COMMENT",
                "comments": [
                    {
                        "path": file_path,
                        "line": c["start_line"],
                        "body": f"**{c['severity'].upper()}** ({c['category']}): {c['comment']}"
                    }
                    for c in comments
                ]
            }
            
            # Post to GitHub
            github_response = await github_service.post_review_comment(
                owner, repo, pull_number, review_comment, installation_id
            )
            
            # Update database with GitHub comment IDs
            with get_db_session() as db_session:
                for i, comment_data in enumerate(comments):
                    comment = db_session.query(ReviewComment).filter(
                        ReviewComment.review_session_id == review_session_id,
                        ReviewComment.file_path == comment_data["path"],
                        ReviewComment.start_line == comment_data["start_line"],
                        ReviewComment.comment == comment_data["comment"]
                    ).first()
                    
                    if comment:
                        comment.github_comment_id = github_response.get("id")
                        comment.github_review_id = github_response.get("id")
                        comment.posted_to_github = True
                        comment.posted_at = datetime.now(timezone.utc)
                
                db_session.commit()
        
        # Post summary comment
        summary_comment = {
            "body": f"## AI Code Review Summary\n\n{review_data['summary']}\n\n**Risk Level:** {review_data['risk']}\n**Recommendation:** {review_data['approval_recommendation']}\n\n*This review was generated by AI and should be used as a starting point for human review.*",
            "event": "COMMENT"
        }
        
        await github_service.post_review_comment(owner, repo, pull_number, summary_comment, installation_id)
        
        logger.info("Comments posted to GitHub successfully", session_id=review_session_id)
        
    except Exception as e:
        logger.error("Failed to post comments to GitHub", error=str(e), session_id=review_session_id)
        raise


async def _create_check_run(owner: str, repo: str, pull_number: int, installation_id: str, review_data: Dict[str, Any], static_analysis_results: Dict[str, Any]):
    """Create or update a check run for the PR."""
    try:
        # Determine check run status
        if review_data["risk"] == "High":
            conclusion = "failure"
        elif review_data["risk"] == "Medium":
            conclusion = "neutral"
        else:
            conclusion = "success"
        
        # Create check run
        check_data = {
            "name": "AI Code Reviewer",
            "head_sha": "latest",  # This should be the actual commit SHA
            "status": "completed",
            "conclusion": conclusion,
            "output": {
                "title": f"AI Code Review - {review_data['risk']} Risk",
                "summary": review_data["summary"],
                "text": f"**Risk Level:** {review_data['risk']}\n**Recommendation:** {review_data['approval_recommendation']}\n**Comments:** {len(review_data['inline_comments'])}"
            }
        }
        
        await github_service.create_check_run(owner, repo, check_data, installation_id)
        
        logger.info("Check run created successfully")
        
    except Exception as e:
        logger.error("Failed to create check run", error=str(e))
        raise


@celery_app.task
def cleanup_old_sessions(days_to_keep: int = 30):
    """Clean up old review sessions and related data."""
    try:
        logger.info("Starting cleanup of old sessions", days_to_keep=days_to_keep)
        
        with get_db_session() as db_session:
            # Clean up old review sessions
            old_sessions = db_session.query(ReviewSession).filter(
                ReviewSession.created_at < datetime.now(timezone.utc).replace(day=days_to_keep)
            ).all()
            
            for session in old_sessions:
                db_session.delete(session)
            
            db_session.commit()
            
            logger.info("Cleanup completed", sessions_deleted=len(old_sessions))
            
    except Exception as e:
        logger.error("Cleanup task failed", error=str(e))
        raise


@celery_app.task
def test_services():
    """Test all services to ensure they're working correctly."""
    try:
        logger.info("Testing services")
        
        # Test AI service
        ai_working = asyncio.run(ai_service.test_connection())
        
        # Test analyzer service
        tools_status = asyncio.run(analyzer_service.test_tools())
        
        # Test database
        from db.session import test_database_connection
        db_working = asyncio.run(test_database_connection())
        
        return {
            "ai_service": ai_working,
            "analyzer_service": tools_status,
            "database": db_working,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error("Service test failed", error=str(e))
        raise


# Periodic tasks
@celery_app.task
def periodic_cleanup():
    """Periodic cleanup task."""
    cleanup_old_sessions.delay()


@celery_app.task
def periodic_health_check():
    """Periodic health check task."""
    test_services.delay()
