"""
Vercel Python function using standard format
"""

import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                "status": "healthy", 
                "message": "AI Code Reviewer Bot",
                "version": "1.0.0",
                "features": ["GitHub webhook", "AI review", "Gemini integration"]
            }
            self.wfile.write(json.dumps(response).encode())
        
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "ok", "timestamp": "2024-01-01T00:00:00Z"}
            self.wfile.write(json.dumps(response).encode())
        
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "not found"}
            self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        if self.path == '/webhook/github':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                event = self.headers.get('X-GitHub-Event', '')
                
                if event == 'pull_request':
                    action = data.get('action')
                    if action in ['opened', 'synchronize']:
                        pr = data.get('pull_request', {})
                        repo = data.get('repository', {})
                        
                        print(f"PR #{pr.get('number')} {action} in {repo.get('full_name')}")
                        
                        # Simple AI review
                        review_text = f"🤖 **AI Code Review**\n\nThis is a test review for PR #{pr.get('number')}. The AI review functionality is working!"
                        print(f"AI Review: {review_text}")
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"status": "success", "message": "Webhook processed"}
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                print(f"Error: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {"status": "error", "message": str(e)}
                self.wfile.write(json.dumps(response).encode())
        
        else:
            self.send_response(404)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {"status": "not found"}
            self.wfile.write(json.dumps(response).encode())