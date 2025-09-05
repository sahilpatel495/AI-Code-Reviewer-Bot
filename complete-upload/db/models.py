"""
Database Models

This module defines the SQLAlchemy models for the AI Code Reviewer Bot.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ReviewSession(Base):
    """Model for tracking review sessions."""
    
    __tablename__ = "review_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String(255), nullable=False, index=True)
    repo = Column(String(255), nullable=False, index=True)
    pull_number = Column(Integer, nullable=False, index=True)
    installation_id = Column(String(255), nullable=False)
    
    # Review metadata
    status = Column(String(50), nullable=False, default="pending")  # pending, in_progress, completed, failed
    risk_level = Column(String(20), nullable=True)  # Low, Medium, High
    approval_recommendation = Column(String(20), nullable=True)  # approve, request_changes, comment
    breaking_changes = Column(Boolean, default=False)
    
    # File information
    files_changed = Column(JSON, nullable=True)  # List of file paths
    languages_detected = Column(JSON, nullable=True)  # Dictionary of language counts
    lines_added = Column(Integer, default=0)
    lines_removed = Column(Integer, default=0)
    
    # AI model information
    ai_model_used = Column(String(100), nullable=True)
    review_duration_seconds = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error information
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Relationships
    comments = relationship("ReviewComment", back_populates="review_session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ReviewSession(id={self.id}, owner={self.owner}, repo={self.repo}, pull_number={self.pull_number}, status={self.status})>"


class ReviewComment(Base):
    """Model for storing review comments."""
    
    __tablename__ = "review_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    review_session_id = Column(Integer, ForeignKey("review_sessions.id"), nullable=False, index=True)
    
    # Comment details
    file_path = Column(String(500), nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    severity = Column(String(20), nullable=False)  # high, medium, low, nit
    category = Column(String(50), nullable=False)  # security, performance, bug, style, architecture, testing
    comment = Column(Text, nullable=False)
    
    # GitHub integration
    github_comment_id = Column(Integer, nullable=True)  # GitHub comment ID if posted
    github_review_id = Column(Integer, nullable=True)  # GitHub review ID if posted
    posted_to_github = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    posted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    review_session = relationship("ReviewSession", back_populates="comments")
    
    def __repr__(self):
        return f"<ReviewComment(id={self.id}, file_path={self.file_path}, line={self.start_line}, severity={self.severity})>"


class RepositoryConfig(Base):
    """Model for storing repository-specific configuration."""
    
    __tablename__ = "repository_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String(255), nullable=False, index=True)
    repo = Column(String(255), nullable=False, index=True)
    
    # Configuration options
    enabled = Column(Boolean, default=True)
    max_comments_per_pr = Column(Integer, default=20)
    focus_areas = Column(JSON, nullable=True)  # List of focus areas (security, performance, etc.)
    excluded_files = Column(JSON, nullable=True)  # List of file patterns to exclude
    custom_prompts = Column(JSON, nullable=True)  # Custom prompt overrides
    
    # AI model preferences
    preferred_model = Column(String(100), nullable=True)  # pro, flash, auto
    temperature = Column(Integer, default=10)  # 0-100 scale
    
    # Static analysis preferences
    enable_python_analyzers = Column(Boolean, default=True)
    enable_js_analyzers = Column(Boolean, default=True)
    enable_java_analyzers = Column(Boolean, default=True)
    enable_sql_analyzers = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<RepositoryConfig(id={self.id}, owner={self.owner}, repo={self.repo}, enabled={self.enabled})>"


class ReviewFeedback(Base):
    """Model for storing feedback on review comments."""
    
    __tablename__ = "review_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    review_comment_id = Column(Integer, ForeignKey("review_comments.id"), nullable=False, index=True)
    
    # Feedback details
    feedback_type = Column(String(20), nullable=False)  # helpful, not_helpful, resolved, ignored
    user_id = Column(String(255), nullable=True)  # GitHub user ID if available
    user_name = Column(String(255), nullable=True)  # GitHub username if available
    
    # Additional context
    comment = Column(Text, nullable=True)  # Optional comment from user
    context = Column(JSON, nullable=True)  # Additional context data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    review_comment = relationship("ReviewComment")
    
    def __repr__(self):
        return f"<ReviewFeedback(id={self.id}, comment_id={self.review_comment_id}, type={self.feedback_type})>"


class WebhookEvent(Base):
    """Model for logging webhook events."""
    
    __tablename__ = "webhook_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Event details
    event_type = Column(String(100), nullable=False, index=True)  # pull_request, push, etc.
    action = Column(String(100), nullable=True)  # opened, synchronize, etc.
    delivery_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Repository information
    owner = Column(String(255), nullable=False, index=True)
    repo = Column(String(255), nullable=False, index=True)
    pull_number = Column(Integer, nullable=True, index=True)
    
    # Processing status
    processed = Column(Boolean, default=False)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_duration_seconds = Column(Integer, nullable=True)
    
    # Error information
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Raw payload (for debugging)
    payload = Column(JSON, nullable=True)
    
    # Timestamps
    received_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<WebhookEvent(id={self.id}, event_type={self.event_type}, delivery_id={self.delivery_id}, processed={self.processed})>"


class SystemMetrics(Base):
    """Model for storing system metrics and statistics."""
    
    __tablename__ = "system_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Metric details
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Integer, nullable=False)
    metric_unit = Column(String(20), nullable=True)  # count, seconds, bytes, etc.
    
    # Context
    context = Column(JSON, nullable=True)  # Additional context data
    tags = Column(JSON, nullable=True)  # Tags for grouping metrics
    
    # Timestamps
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    
    def __repr__(self):
        return f"<SystemMetrics(id={self.id}, name={self.metric_name}, value={self.metric_value}, recorded_at={self.recorded_at})>"


class RateLimit(Base):
    """Model for tracking rate limits and usage."""
    
    __tablename__ = "rate_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Rate limit details
    resource_type = Column(String(50), nullable=False, index=True)  # github_api, gemini_api, etc.
    resource_id = Column(String(255), nullable=False, index=True)  # installation_id, api_key, etc.
    
    # Usage tracking
    requests_made = Column(Integer, default=0)
    requests_limit = Column(Integer, nullable=True)
    reset_time = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<RateLimit(id={self.id}, resource_type={self.resource_type}, resource_id={self.resource_id}, requests_made={self.requests_made})>"
