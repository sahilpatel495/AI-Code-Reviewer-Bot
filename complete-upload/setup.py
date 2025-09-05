"""
Setup script for AI Code Reviewer Bot
"""

import os
import shutil
from pathlib import Path

def setup_environment():
    """Set up the environment for the AI Code Reviewer Bot."""
    
    print("🚀 Setting up AI Code Reviewer Bot...")
    
    # Check if .env exists, if not copy from local.env
    if not os.path.exists('.env'):
        if os.path.exists('local.env'):
            shutil.copy('local.env', '.env')
            print("✅ Created .env file from local.env template")
        else:
            print("❌ local.env template not found")
            return False
    else:
        print("✅ .env file already exists")
    
    # Create necessary directories
    directories = ['logs', 'tmp', 'db']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Create SQLite database if using SQLite
    if os.getenv('DATABASE_URL', '').startswith('sqlite'):
        print("✅ SQLite database will be created automatically")
    
    print("\n🎉 Setup completed!")
    print("\n📝 Next steps:")
    print("1. Edit .env file with your API keys and configuration")
    print("2. Get your Gemini API key from: https://makersuite.google.com/app/apikey")
    print("3. Create a GitHub App and get credentials")
    print("4. Run: python app.py")
    
    return True

if __name__ == "__main__":
    setup_environment()
