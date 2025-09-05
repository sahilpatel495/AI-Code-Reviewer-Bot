-- AI Code Reviewer Bot - Database Initialization Script

-- Create database if it doesn't exist
CREATE DATABASE IF NOT EXISTS ai_reviewer;

-- Use the database
\c ai_reviewer;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance
-- These will be created by SQLAlchemy, but we can add custom ones here

-- Index for review sessions by repository
CREATE INDEX IF NOT EXISTS idx_review_sessions_repo 
ON review_sessions (owner, repo, pull_number);

-- Index for review sessions by status
CREATE INDEX IF NOT EXISTS idx_review_sessions_status 
ON review_sessions (status, created_at);

-- Index for review comments by session
CREATE INDEX IF NOT EXISTS idx_review_comments_session 
ON review_comments (review_session_id, created_at);

-- Index for webhook events by delivery ID
CREATE INDEX IF NOT EXISTS idx_webhook_events_delivery 
ON webhook_events (delivery_id);

-- Index for webhook events by repository
CREATE INDEX IF NOT EXISTS idx_webhook_events_repo 
ON webhook_events (owner, repo, pull_number);

-- Index for system metrics by name and time
CREATE INDEX IF NOT EXISTS idx_system_metrics_name_time 
ON system_metrics (metric_name, recorded_at);

-- Index for rate limits by resource
CREATE INDEX IF NOT EXISTS idx_rate_limits_resource 
ON rate_limits (resource_type, resource_id);

-- Create a function to clean up old data
CREATE OR REPLACE FUNCTION cleanup_old_data(days_to_keep INTEGER DEFAULT 30)
RETURNS VOID AS $$
BEGIN
    -- Clean up old webhook events
    DELETE FROM webhook_events 
    WHERE received_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    -- Clean up old system metrics
    DELETE FROM system_metrics 
    WHERE recorded_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    -- Clean up old rate limit records
    DELETE FROM rate_limits 
    WHERE updated_at < NOW() - INTERVAL '1 day' * days_to_keep;
    
    -- Clean up old review sessions (keep for longer)
    DELETE FROM review_sessions 
    WHERE created_at < NOW() - INTERVAL '1 day' * (days_to_keep * 2);
END;
$$ LANGUAGE plpgsql;

-- Create a function to get review statistics
CREATE OR REPLACE FUNCTION get_review_stats()
RETURNS TABLE (
    total_reviews BIGINT,
    completed_reviews BIGINT,
    failed_reviews BIGINT,
    avg_duration NUMERIC,
    reviews_today BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_reviews,
        COUNT(*) FILTER (WHERE status = 'completed') as completed_reviews,
        COUNT(*) FILTER (WHERE status = 'failed') as failed_reviews,
        AVG(review_duration_seconds) as avg_duration,
        COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE) as reviews_today
    FROM review_sessions;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get comment statistics
CREATE OR REPLACE FUNCTION get_comment_stats()
RETURNS TABLE (
    total_comments BIGINT,
    high_severity BIGINT,
    medium_severity BIGINT,
    low_severity BIGINT,
    nit_comments BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_comments,
        COUNT(*) FILTER (WHERE severity = 'high') as high_severity,
        COUNT(*) FILTER (WHERE severity = 'medium') as medium_severity,
        COUNT(*) FILTER (WHERE severity = 'low') as low_severity,
        COUNT(*) FILTER (WHERE severity = 'nit') as nit_comments
    FROM review_comments;
END;
$$ LANGUAGE plpgsql;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE ai_reviewer TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO postgres;
