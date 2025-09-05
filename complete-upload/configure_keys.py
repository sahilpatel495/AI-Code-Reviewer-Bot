"""
Interactive script to configure API keys for the AI Code Reviewer Bot
"""

import os
import sys
from pathlib import Path

def configure_api_keys():
    """Interactive configuration of API keys."""
    
    print("🔑 AI Code Reviewer Bot - API Key Configuration")
    print("=" * 50)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("❌ .env file not found. Please run setup.py first.")
        return False
    
    print("📝 Let's configure your API keys...")
    print()
    
    # Read current .env file
    with open('.env', 'r') as f:
        content = f.read()
    
    # Configure Gemini API Key
    print("🤖 Gemini AI Configuration")
    print("-" * 30)
    print("1. Go to: https://makersuite.google.com/app/apikey")
    print("2. Sign in and create an API key")
    print("3. Copy the API key")
    print()
    
    gemini_key = input("Enter your Gemini API key (or press Enter to skip): ").strip()
    if gemini_key:
        content = content.replace('GEMINI_API_KEY=your_gemini_api_key_here', f'GEMINI_API_KEY={gemini_key}')
        print("✅ Gemini API key configured")
    else:
        print("⚠️  Skipped Gemini API key configuration")
    
    print()
    
    # Configure GitHub App
    print("🐙 GitHub App Configuration")
    print("-" * 30)
    print("1. Go to: https://github.com/settings/apps")
    print("2. Click 'New GitHub App'")
    print("3. Set permissions: Read (contents, metadata, pull requests), Write (pull request comments, commit statuses, checks)")
    print("4. Set webhook URL: http://localhost:8000/webhook/github (for testing)")
    print("5. Copy the App ID and generate a private key")
    print()
    
    github_app_id = input("Enter your GitHub App ID (or press Enter to skip): ").strip()
    if github_app_id:
        content = content.replace('GITHUB_APP_ID=your_github_app_id_here', f'GITHUB_APP_ID={github_app_id}')
        print("✅ GitHub App ID configured")
    else:
        print("⚠️  Skipped GitHub App ID configuration")
    
    print()
    
    # Configure GitHub Private Key
    print("🔐 GitHub Private Key Configuration")
    print("-" * 30)
    print("You can either:")
    print("1. Paste the private key content directly")
    print("2. Provide the path to the private key file")
    print()
    
    private_key_input = input("Enter private key content or file path (or press Enter to skip): ").strip()
    if private_key_input:
        if private_key_input.startswith('-----BEGIN'):
            # It's the key content
            content = content.replace('GITHUB_APP_PRIVATE_KEY=your_private_key_content_or_path_here', f'GITHUB_APP_PRIVATE_KEY={private_key_input}')
            print("✅ GitHub private key configured")
        elif os.path.exists(private_key_input):
            # It's a file path
            content = content.replace('GITHUB_APP_PRIVATE_KEY=your_private_key_content_or_path_here', f'GITHUB_APP_PRIVATE_KEY={private_key_input}')
            print("✅ GitHub private key file path configured")
        else:
            print("⚠️  Invalid private key input")
    else:
        print("⚠️  Skipped GitHub private key configuration")
    
    print()
    
    # Configure Webhook Secret
    webhook_secret = input("Enter your GitHub webhook secret (or press Enter to skip): ").strip()
    if webhook_secret:
        content = content.replace('GITHUB_WEBHOOK_SECRET=your_webhook_secret_here', f'GITHUB_WEBHOOK_SECRET={webhook_secret}')
        print("✅ GitHub webhook secret configured")
    else:
        print("⚠️  Skipped GitHub webhook secret configuration")
    
    # Write updated .env file
    with open('.env', 'w') as f:
        f.write(content)
    
    print()
    print("🎉 Configuration completed!")
    print()
    print("📋 Next steps:")
    print("1. Run: python test_setup.py (to verify configuration)")
    print("2. Run: python app.py (to start the application)")
    print("3. Test with: curl http://localhost:8000/health")
    
    return True

if __name__ == "__main__":
    try:
        configure_api_keys()
    except KeyboardInterrupt:
        print("\n\n❌ Configuration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Configuration failed: {e}")
        sys.exit(1)
