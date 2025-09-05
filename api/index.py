"""
AI Code Reviewer Bot - Vercel Serverless Function
"""

import json
import os
import httpx
import google.generativeai as genai

def handler(request):
    # Get the path and method
    path = request.get('path', '/')
    method = request.get('method', 'GET')
    
    # Handle async functions properly
    import asyncio
    
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
                    
                    # Trigger AI review (simplified for now)
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(process_pr_review(pr, repo, data))
                        loop.close()
                    except Exception as e:
                        print(f"Error in async processing: {e}")
            
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

async def process_pr_review(pr, repo, webhook_data):
    """Process PR review using AI"""
    try:
        # Get environment variables
        github_token = os.getenv('GITHUB_TOKEN')
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        if not gemini_api_key:
            print("Gemini API key not configured")
            return
        
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Get PR details
        pr_number = pr.get('number')
        pr_title = pr.get('title', '')
        pr_body = pr.get('body', '')
        
        # Create a simple review prompt
        prompt = f"""
        Review this Pull Request:
        
        Title: {pr_title}
        Description: {pr_body}
        
        Please provide a brief code review focusing on:
        1. Code quality and best practices
        2. Potential bugs or issues
        3. Suggestions for improvement
        
        Keep the review concise and actionable.
        """
        
        # Generate AI review
        response = model.generate_content(prompt)
        review_text = response.text
        
        # Post comment to GitHub (if token is available)
        if github_token:
            await post_github_comment(repo, pr_number, review_text, github_token)
        else:
            print(f"AI Review: {review_text}")
            
    except Exception as e:
        print(f"Error in AI review: {e}")

async def post_github_comment(repo, pr_number, comment, token):
    """Post comment to GitHub PR"""
    try:
        url = f"https://api.github.com/repos/{repo.get('full_name')}/issues/{pr_number}/comments"
        
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        data = {
            'body': f"🤖 **AI Code Review**\n\n{comment}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            
        if response.status_code == 201:
            print(f"Comment posted to PR #{pr_number}")
        else:
            print(f"Failed to post comment: {response.status_code}")
            
    except Exception as e:
        print(f"Error posting comment: {e}")