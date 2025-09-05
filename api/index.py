"""
Minimal Vercel Python functione url ?
"""

def handler(request):
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': '{"message": "Hello from AI Code Reviewer Bot!", "status": "working"}'
    }