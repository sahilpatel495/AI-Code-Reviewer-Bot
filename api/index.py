"""
Basic Vercel Python function
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
            'body': json.dumps({"status": "healthy", "message": "AI Code Reviewer Bot"})
        }
    
    elif path == '/health' and method == 'GET':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({"status": "ok"})
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
                    print(f"PR #{pr.get('number')} {action}")
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({"status": "success"})
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