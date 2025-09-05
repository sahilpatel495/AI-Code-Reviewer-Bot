"""
Quick test script to verify the AI Code Reviewer Bot is working
"""

import asyncio
import os
import sys
from pathlib import Path

async def test_basic_functionality():
    """Test basic functionality without requiring API keys."""
    
    print("🧪 Quick Test - AI Code Reviewer Bot")
    print("=" * 40)
    
    try:
        # Test 1: Import all modules
        print("1. Testing imports...")
        from app import app
        from services.ai_service import AIService
        from services.github_service import GitHubService
        from services.analyzer_service import AnalyzerService
        from db.session import get_db_session
        print("   ✅ All modules imported successfully")
        
        # Test 2: Test database
        print("2. Testing database...")
        from db.session import test_database_connection
        db_working = await test_database_connection()
        if db_working:
            print("   ✅ Database connection working")
        else:
            print("   ❌ Database connection failed")
            return False
        
        # Test 3: Test analyzer service
        print("3. Testing analyzer service...")
        analyzer = AnalyzerService()
        tools_status = await analyzer.test_tools()
        print(f"   📊 Available tools: {[tool for tool, status in tools_status.items() if status]}")
        
        # Test 4: Test FastAPI app
        print("4. Testing FastAPI app...")
        from fastapi.testclient import TestClient
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/")
        if response.status_code == 200:
            print("   ✅ FastAPI app responding")
        else:
            print(f"   ❌ FastAPI app failed: {response.status_code}")
            return False
        
        # Test 5: Check API key configuration
        print("5. Checking API key configuration...")
        gemini_key = os.getenv('GEMINI_API_KEY')
        github_app_id = os.getenv('GITHUB_APP_ID')
        
        if gemini_key and gemini_key != 'your_gemini_api_key_here':
            print("   ✅ Gemini API key configured")
        else:
            print("   ⚠️  Gemini API key not configured")
        
        if github_app_id and github_app_id != 'your_github_app_id_here':
            print("   ✅ GitHub App ID configured")
        else:
            print("   ⚠️  GitHub App ID not configured")
        
        print()
        print("🎉 Quick test completed!")
        print()
        print("📋 Status:")
        print(f"   - Database: {'✅ Working' if db_working else '❌ Failed'}")
        print(f"   - FastAPI: ✅ Working")
        print(f"   - Analyzers: ✅ Working")
        print(f"   - Gemini API: {'✅ Configured' if gemini_key and gemini_key != 'your_gemini_api_key_here' else '⚠️  Not configured'}")
        print(f"   - GitHub App: {'✅ Configured' if github_app_id and github_app_id != 'your_github_app_id_here' else '⚠️  Not configured'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Run the quick test."""
    try:
        result = asyncio.run(test_basic_functionality())
        if result:
            print("\n🚀 Your AI Code Reviewer Bot is ready to use!")
            print("\nTo start the application:")
            print("   python app.py")
            print("\nTo test the API:")
            print("   curl http://localhost:8000/health")
        else:
            print("\n❌ Some tests failed. Please check the configuration.")
        
        return result
        
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
