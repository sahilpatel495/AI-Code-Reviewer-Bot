"""
Test script to verify the AI Code Reviewer Bot setup
"""

import os
import sys
from pathlib import Path

def test_imports():
    """Test if all required packages can be imported."""
    print("🧪 Testing package imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
        return False
    
    try:
        import google.generativeai as genai
        print("✅ Google Generative AI imported successfully")
    except ImportError as e:
        print(f"❌ Google Generative AI import failed: {e}")
        return False
    
    try:
        import celery
        print("✅ Celery imported successfully")
    except ImportError as e:
        print(f"❌ Celery import failed: {e}")
        return False
    
    try:
        import sqlalchemy
        print("✅ SQLAlchemy imported successfully")
    except ImportError as e:
        print(f"❌ SQLAlchemy import failed: {e}")
        return False
    
    try:
        import redis
        print("✅ Redis imported successfully")
    except ImportError as e:
        print(f"❌ Redis import failed: {e}")
        return False
    
    return True

def test_environment():
    """Test environment configuration."""
    print("\n🔧 Testing environment configuration...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        return False
    else:
        print("✅ .env file exists")
    
    # Check if required directories exist
    required_dirs = ['logs', 'tmp', 'db']
    for directory in required_dirs:
        if not os.path.exists(directory):
            print(f"❌ Directory {directory} not found")
            return False
        else:
            print(f"✅ Directory {directory} exists")
    
    return True

def test_ai_service():
    """Test AI service connection."""
    print("\n🤖 Testing AI service...")
    
    try:
        from services.ai_service import AIService
        
        # Check if API key is set
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key or api_key == 'your_gemini_api_key_here':
            print("⚠️  Gemini API key not configured (set GEMINI_API_KEY in .env)")
            return False
        
        # Try to initialize the service
        ai_service = AIService()
        print("✅ AI service initialized successfully")
        
        # Test connection (this will fail if API key is invalid)
        import asyncio
        try:
            result = asyncio.run(ai_service.test_connection())
            if result:
                print("✅ AI service connection test passed")
            else:
                print("⚠️  AI service connection test failed (check API key)")
        except Exception as e:
            print(f"⚠️  AI service connection test failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI service test failed: {e}")
        return False

def test_github_service():
    """Test GitHub service configuration."""
    print("\n🐙 Testing GitHub service...")
    
    try:
        from services.github_service import GitHubService
        
        # Check if GitHub credentials are set
        app_id = os.getenv('GITHUB_APP_ID')
        private_key = os.getenv('GITHUB_APP_PRIVATE_KEY')
        webhook_secret = os.getenv('GITHUB_WEBHOOK_SECRET')
        
        if not app_id or app_id == 'your_github_app_id_here':
            print("⚠️  GitHub App ID not configured (set GITHUB_APP_ID in .env)")
            return False
        
        if not private_key or private_key == 'your_private_key_content_or_path_here':
            print("⚠️  GitHub App private key not configured (set GITHUB_APP_PRIVATE_KEY in .env)")
            return False
        
        if not webhook_secret or webhook_secret == 'your_webhook_secret_here':
            print("⚠️  GitHub webhook secret not configured (set GITHUB_WEBHOOK_SECRET in .env)")
            return False
        
        print("✅ GitHub service configuration looks good")
        return True
        
    except Exception as e:
        print(f"❌ GitHub service test failed: {e}")
        return False

def test_database():
    """Test database connection."""
    print("\n🗄️  Testing database...")
    
    try:
        from db.session import test_database_connection
        import asyncio
        
        result = asyncio.run(test_database_connection())
        if result:
            print("✅ Database connection test passed")
        else:
            print("❌ Database connection test failed")
        
        return result
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 AI Code Reviewer Bot - Setup Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_environment,
        test_ai_service,
        test_github_service,
        test_database
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
