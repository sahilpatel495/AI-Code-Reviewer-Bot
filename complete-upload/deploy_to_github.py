"""
Script to help deploy the AI Code Reviewer Bot to GitHub
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_git_status():
    """Check if git is initialized and configured."""
    print("🔍 Checking git status...")
    
    # Check if git is initialized
    if not os.path.exists('.git'):
        print("📁 Initializing git repository...")
        if not run_command("git init", "Git initialization"):
            return False
    
    # Check git config
    try:
        result = subprocess.run("git config user.name", shell=True, capture_output=True, text=True)
        if not result.stdout.strip():
            print("⚠️  Git user.name not configured")
            name = input("Enter your git username: ").strip()
            if name:
                run_command(f'git config user.name "{name}"', "Setting git username")
        
        result = subprocess.run("git config user.email", shell=True, capture_output=True, text=True)
        if not result.stdout.strip():
            print("⚠️  Git user.email not configured")
            email = input("Enter your git email: ").strip()
            if email:
                run_command(f'git config user.email "{email}"', "Setting git email")
        
        print("✅ Git configuration looks good")
        return True
        
    except Exception as e:
        print(f"❌ Git configuration check failed: {e}")
        return False

def create_gitignore():
    """Create .gitignore file."""
    gitignore_content = """# Environment variables
.env
*.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Database
*.db
*.sqlite
*.sqlite3

# Temporary files
tmp/
temp/

# Vercel
.vercel/
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    
    print("✅ Created .gitignore file")

def deploy_to_github():
    """Deploy the project to GitHub."""
    
    print("🚀 Deploying AI Code Reviewer Bot to GitHub")
    print("=" * 50)
    
    # Check git status
    if not check_git_status():
        return False
    
    # Create .gitignore
    create_gitignore()
    
    # Add all files
    if not run_command("git add .", "Adding files to git"):
        return False
    
    # Check if there are changes to commit
    try:
        result = subprocess.run("git diff --cached --quiet", shell=True, capture_output=True)
        if result.returncode == 0:
            print("ℹ️  No changes to commit")
        else:
            # Commit changes
            if not run_command('git commit -m "Initial commit: AI Code Reviewer Bot"', "Committing changes"):
                return False
    except Exception as e:
        print(f"❌ Error checking git status: {e}")
        return False
    
    # Get repository URL
    print("\n📋 GitHub Repository Setup")
    print("-" * 30)
    print("1. Go to GitHub.com and create a new repository")
    print("2. Copy the repository URL (e.g., https://github.com/username/repo-name.git)")
    print("3. Make sure the repository is private (recommended)")
    print()
    
    repo_url = input("Enter your GitHub repository URL: ").strip()
    if not repo_url:
        print("❌ Repository URL is required")
        return False
    
    # Add remote origin
    if not run_command(f"git remote add origin {repo_url}", "Adding remote origin"):
        # If remote already exists, update it
        run_command(f"git remote set-url origin {repo_url}", "Updating remote origin")
    
    # Push to GitHub
    if not run_command("git push -u origin main", "Pushing to GitHub"):
        # Try with master branch if main fails
        print("🔄 Trying with master branch...")
        if not run_command("git push -u origin master", "Pushing to GitHub (master branch)"):
            return False
    
    print("\n🎉 Successfully deployed to GitHub!")
    print(f"📁 Repository: {repo_url}")
    print("\n📋 Next steps:")
    print("1. Go to Vercel.com and connect your GitHub repository")
    print("2. Follow the VERCEL_DEPLOYMENT.md guide")
    print("3. Set up your environment variables in Vercel")
    print("4. Deploy your app!")
    
    return True

def main():
    """Main function."""
    try:
        success = deploy_to_github()
        if success:
            print("\n✅ Deployment completed successfully!")
        else:
            print("\n❌ Deployment failed. Please check the errors above.")
        
        return success
        
    except KeyboardInterrupt:
        print("\n\n❌ Deployment cancelled by user")
        return False
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
