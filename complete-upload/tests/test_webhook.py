"""
Tests for GitHub webhook handling.
"""

import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app import app
from config.settings import settings

client = TestClient(app)


class TestWebhookHandling:
    """Test cases for webhook handling."""
    
    def test_webhook_signature_verification(self):
        """Test webhook signature verification."""
        # This would test the signature verification logic
        # Implementation depends on the actual signature verification method
        pass
    
    def test_pull_request_opened_webhook(self):
        """Test handling of pull request opened webhook."""
        with patch('jobs.review_task.process_pr_review.delay') as mock_task:
            payload = {
                "action": "opened",
                "pull_request": {
                    "number": 123,
                    "title": "Test PR",
                    "body": "Test description"
                },
                "repository": {
                    "name": "test-repo",
                    "owner": {
                        "login": "test-user"
                    }
                },
                "installation": {
                    "id": "12345"
                }
            }
            
            # Mock signature verification
            with patch('app.verify_github_signature', return_value=True):
                response = client.post(
                    "/webhook/github",
                    json=payload,
                    headers={
                        "X-GitHub-Event": "pull_request",
                        "X-GitHub-Delivery": "test-delivery-id",
                        "X-Hub-Signature-256": "sha256=test-signature"
                    }
                )
            
            assert response.status_code == 200
            assert response.json()["status"] == "accepted"
            mock_task.assert_called_once()
    
    def test_pull_request_synchronize_webhook(self):
        """Test handling of pull request synchronize webhook."""
        with patch('jobs.review_task.process_pr_review.delay') as mock_task:
            payload = {
                "action": "synchronize",
                "pull_request": {
                    "number": 123,
                    "title": "Test PR",
                    "body": "Test description"
                },
                "repository": {
                    "name": "test-repo",
                    "owner": {
                        "login": "test-user"
                    }
                },
                "installation": {
                    "id": "12345"
                }
            }
            
            with patch('app.verify_github_signature', return_value=True):
                response = client.post(
                    "/webhook/github",
                    json=payload,
                    headers={
                        "X-GitHub-Event": "pull_request",
                        "X-GitHub-Delivery": "test-delivery-id",
                        "X-Hub-Signature-256": "sha256=test-signature"
                    }
                )
            
            assert response.status_code == 200
            assert response.json()["status"] == "accepted"
            mock_task.assert_called_once()
    
    def test_invalid_signature(self):
        """Test handling of invalid webhook signature."""
        payload = {"test": "data"}
        
        with patch('app.verify_github_signature', return_value=False):
            response = client.post(
                "/webhook/github",
                json=payload,
                headers={
                    "X-GitHub-Event": "pull_request",
                    "X-GitHub-Delivery": "test-delivery-id",
                    "X-Hub-Signature-256": "sha256=invalid-signature"
                }
            )
        
        assert response.status_code == 401
        assert "Invalid signature" in response.json()["detail"]
    
    def test_unsupported_event_type(self):
        """Test handling of unsupported event types."""
        payload = {"test": "data"}
        
        with patch('app.verify_github_signature', return_value=True):
            response = client.post(
                "/webhook/github",
                json=payload,
                headers={
                    "X-GitHub-Event": "unsupported_event",
                    "X-GitHub-Delivery": "test-delivery-id",
                    "X-Hub-Signature-256": "sha256=test-signature"
                }
            )
        
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"
    
    def test_missing_required_data(self):
        """Test handling of webhook with missing required data."""
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 123
            }
            # Missing repository and installation data
        }
        
        with patch('app.verify_github_signature', return_value=True):
            response = client.post(
                "/webhook/github",
                json=payload,
                headers={
                    "X-GitHub-Event": "pull_request",
                    "X-GitHub-Delivery": "test-delivery-id",
                    "X-Hub-Signature-256": "sha256=test-signature"
                }
            )
        
        assert response.status_code == 400
        assert "Missing required data" in response.json()["detail"]
    
    def test_invalid_json_payload(self):
        """Test handling of invalid JSON payload."""
        with patch('app.verify_github_signature', return_value=True):
            response = client.post(
                "/webhook/github",
                data="invalid json",
                headers={
                    "X-GitHub-Event": "pull_request",
                    "X-GitHub-Delivery": "test-delivery-id",
                    "X-Hub-Signature-256": "sha256=test-signature"
                }
            )
        
        assert response.status_code == 400
        assert "Invalid JSON payload" in response.json()["detail"]


class TestManualReviewTrigger:
    """Test cases for manual review triggering."""
    
    def test_trigger_review_success(self):
        """Test successful manual review trigger."""
        with patch('services.github_service.GitHubService.get_installation_id', return_value="12345"), \
             patch('jobs.review_task.process_pr_review.delay') as mock_task:
            
            response = client.post(
                "/review",
                json={
                    "owner": "test-user",
                    "repo": "test-repo",
                    "pull_number": 123
                }
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "accepted"
            mock_task.assert_called_once()
    
    def test_trigger_review_not_installed(self):
        """Test manual review trigger when app is not installed."""
        with patch('services.github_service.GitHubService.get_installation_id', return_value=None):
            response = client.post(
                "/review",
                json={
                    "owner": "test-user",
                    "repo": "test-repo",
                    "pull_number": 123
                }
            )
            
            assert response.status_code == 404
            assert "not installed" in response.json()["detail"]
    
    def test_trigger_review_with_focus_area(self):
        """Test manual review trigger with focus area."""
        with patch('services.github_service.GitHubService.get_installation_id', return_value="12345"), \
             patch('jobs.review_task.process_pr_review.delay') as mock_task:
            
            response = client.post(
                "/review",
                json={
                    "owner": "test-user",
                    "repo": "test-repo",
                    "pull_number": 123,
                    "focus_area": "security"
                }
            )
            
            assert response.status_code == 200
            assert response.json()["status"] == "accepted"
            mock_task.assert_called_once()


class TestHealthEndpoints:
    """Test cases for health check endpoints."""
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["app"] == settings.app_name
        assert data["version"] == settings.app_version
    
    def test_health_check_endpoint(self):
        """Test health check endpoint."""
        with patch('db.session.get_db_session') as mock_db, \
             patch('redis.from_url') as mock_redis:
            
            # Mock database connection
            mock_db.return_value.__enter__.return_value.execute.return_value = None
            
            # Mock Redis connection
            mock_redis.return_value.ping.return_value = True
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "components" in data
            assert "database" in data["components"]
            assert "redis" in data["components"]
    
    def test_health_check_database_failure(self):
        """Test health check when database is down."""
        with patch('db.session.get_db_session', side_effect=Exception("Database error")):
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["components"]["database"] == "unhealthy"
    
    def test_health_check_redis_failure(self):
        """Test health check when Redis is down."""
        with patch('db.session.get_db_session') as mock_db, \
             patch('redis.from_url', side_effect=Exception("Redis error")):
            
            mock_db.return_value.__enter__.return_value.execute.return_value = None
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["components"]["redis"] == "unhealthy"


class TestReviewStatus:
    """Test cases for review status endpoint."""
    
    def test_get_review_status_success(self):
        """Test successful review status retrieval."""
        with patch('db.session.get_db_session') as mock_db:
            # Mock database session and query results
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session
            
            # Mock review session
            mock_review_session = MagicMock()
            mock_review_session.id = 1
            mock_review_session.status = "completed"
            mock_review_session.created_at = "2024-01-01T00:00:00Z"
            mock_review_session.completed_at = "2024-01-01T00:05:00Z"
            mock_review_session.risk_level = "Low"
            mock_review_session.approval_recommendation = "approve"
            
            # Mock comments
            mock_comment = MagicMock()
            mock_comment.id = 1
            mock_comment.file_path = "test.py"
            mock_comment.start_line = 10
            mock_comment.end_line = 10
            mock_comment.severity = "low"
            mock_comment.category = "style"
            mock_comment.comment = "Test comment"
            mock_comment.created_at = "2024-01-01T00:00:00Z"
            
            mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_review_session
            mock_session.query.return_value.filter.return_value.all.return_value = [mock_comment]
            
            response = client.get("/reviews/test-user/test-repo/123")
            
            assert response.status_code == 200
            data = response.json()
            assert "review_session" in data
            assert "comments" in data
            assert data["review_session"]["status"] == "completed"
            assert len(data["comments"]) == 1
    
    def test_get_review_status_not_found(self):
        """Test review status when session not found."""
        with patch('db.session.get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session
            mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
            
            response = client.get("/reviews/test-user/test-repo/123")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]


class TestStats:
    """Test cases for stats endpoint."""
    
    def test_get_stats_success(self):
        """Test successful stats retrieval."""
        with patch('db.session.get_db_session') as mock_db:
            mock_session = MagicMock()
            mock_db.return_value.__enter__.return_value = mock_session
            
            # Mock query results
            mock_session.query.return_value.count.return_value = 100
            mock_session.query.return_value.filter.return_value.count.return_value = 95
            
            response = client.get("/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert "total_reviews" in data
            assert "completed_reviews" in data
            assert "success_rate" in data
            assert "reviews_today" in data
            assert data["total_reviews"] == 100
            assert data["completed_reviews"] == 95
            assert data["success_rate"] == 95.0
