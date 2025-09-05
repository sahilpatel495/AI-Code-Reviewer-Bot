"""
Startup script for AI Code Reviewer Bot
This script will start the application with proper error handling
"""

import os
import sys
from pathlib import Path

def check_environment():
    """Check if the environment is properly configured."""
    
    print("🔍 Checking environment configuration...")
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please run setup.py first.")
        return False
    
    # Check if required directories exist
    required_dirs = ['logs', 'tmp', 'db']
    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"❌ Directory {directory} not found. Please run setup.py first.")
            return False
    
    print("✅ Environment configuration looks good")
    return True

def start_application():
    """Start the FastAPI application."""
    
    print("🚀 Starting AI Code Reviewer Bot...")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        return False
    
    # Check API key configuration
    gemini_key = os.getenv('GITHUB_APP_ID')
    github_app_id = os.getenv('GITHUB_APP_ID')
    
    if not gemini_key or gemini_key == 'your_gemini_api_key_here':
        print("⚠️  Gemini API key not configured")
        print("   Run: python configure_keys.py")
        print()
    
    if not github_app_id or github_app_id == 'your_github_app_id_here':
        print("⚠️  GitHub App not configured")
        print("   Run: python configure_keys.py")
        print()
    
    print("🌐 Starting FastAPI server...")
    print("📡 Server will be available at: http://localhost:8000")
    print("📊 Health check: http://localhost:8000/health")
    print("📚 API docs: http://localhost:8000/docs")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Import and run the app
        import uvicorn
        from app import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
        return True
    except Exception as e:
        print(f"\n❌ Failed to start server: {e}")
        return False

def main():
    """Main function."""
    try:
        return start_application()
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
