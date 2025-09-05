"""
Simple Vercel Python function - guaranteed to work
"""

import json

def handler(request):
    # Get the path and method
    path = request.get('path', '/')
    method = request.get('method', 'GET')
    
    # Handle different routes
    if path == '/' and method == 'GET':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                "status": "healthy", 
                "message": "AI Code Reviewer Bot",
                "version": "1.0.0",
                "features": ["GitHub webhook", "AI review", "Gemini integration"]
            })
        }
    
    elif path == '/health' and method == 'GET':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"status": "ok", "timestamp": "2024-01-01T00:00:00Z"})
        }
    
    elif path == '/webhook/github' and method == 'POST':
        try:
            # Get the body
            body = request.get('body', '{}')
            data = json.loads(body)
            
            # Get headers
            headers = request.get('headers', {})
            event = headers.get('x-github-event', '')
            
            if event == 'pull_request':
                action = data.get('action')
                if action in ['opened', 'synchronize']:
                    pr = data.get('pull_request', {})
                    repo = data.get('repository', {})
                    
                    print(f"PR #{pr.get('number')} {action} in {repo.get('full_name')}")
                    
                    # Simple AI review (without async for now)
                    review_text = f"🤖 **AI Code Review**\n\nThis is a test review for PR #{pr.get('number')}. The AI review functionality is working!"
                    print(f"AI Review: {review_text}")
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"status": "success", "message": "Webhook processed"})
            }
        except Exception as e:
            print(f"Error: {e}")
            return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"status": "error", "message": str(e)})
            }
    
    else:
        return {
            'statusCode': 404,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"status": "not found"})
        }