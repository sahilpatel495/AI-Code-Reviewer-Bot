"""
Script to help copy files to GitHub repository
"""

import os
import shutil
import subprocess
from pathlib import Path

def copy_files_to_github_repo():
    """Copy all files to a GitHub repository."""
    
    print("🔄 Copying files to GitHub repository...")
    print("=" * 50)
    
    # Get current directory
    current_dir = Path.cwd()
    print(f"📁 Current directory: {current_dir}")
    
    # Ask for GitHub repository path
    print("\n📋 GitHub Repository Setup")
    print("-" * 30)
    print("1. Go to your GitHub repository in the browser")
    print("2. Click the green 'Code' button")
    print("3. Copy the repository URL")
    print("4. Clone it to your local machine")
    print()
    
    github_repo_path = input("Enter the path to your cloned GitHub repository: ").strip()
    
    if not github_repo_path:
        print("❌ Repository path is required")
        return False
    
    # Check if the path exists
    if not os.path.exists(github_repo_path):
        print(f"❌ Path does not exist: {github_repo_path}")
        return False
    
    # Check if it's a git repository
    if not os.path.exists(os.path.join(github_repo_path, '.git')):
        print(f"❌ Not a git repository: {github_repo_path}")
        return False
    
    print(f"✅ Found git repository: {github_repo_path}")
    
    # List of files to copy (excluding git and sensitive files)
    files_to_copy = [
        'app.py',
        'requirements.txt',
        'requirements-vercel.txt',
        'vercel.json',
        'api/',
        'config/',
        'services/',
        'db/',
        'jobs/',
        'tests/',
        'Dockerfile',
        'docker-compose.yml',
        'nginx.conf',
        'entrypoint.sh',
        'setup.py',
        'test_setup.py',
        'quick_test.py',
        'start_app.py',
        'configure_keys.py',
        'deploy_to_github.py',
        'README.md',
        'SETUP_GUIDE.md',
        'VERCEL_DEPLOYMENT.md',
        'vercel-env.example',
        'config.env.example',
        'local.env'
    ]
    
    # Copy files
    copied_files = []
    skipped_files = []
    
    for file_path in files_to_copy:
        source = current_dir / file_path
        destination = Path(github_repo_path) / file_path
        
        try:
            if source.is_file():
                # Copy file
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                copied_files.append(file_path)
                print(f"✅ Copied: {file_path}")
            elif source.is_dir():
                # Copy directory
                if destination.exists():
                    shutil.rmtree(destination)
                shutil.copytree(source, destination)
                copied_files.append(file_path)
                print(f"✅ Copied: {file_path}/")
            else:
                skipped_files.append(file_path)
                print(f"⚠️  Skipped: {file_path} (not found)")
        except Exception as e:
            print(f"❌ Failed to copy {file_path}: {e}")
            skipped_files.append(file_path)
    
    print(f"\n📊 Copy Summary:")
    print(f"   ✅ Copied: {len(copied_files)} items")
    print(f"   ⚠️  Skipped: {len(skipped_files)} items")
    
    if skipped_files:
        print(f"\n⚠️  Skipped files: {', '.join(skipped_files)}")
    
    print(f"\n🎉 Files copied successfully!")
    print(f"📁 Repository location: {github_repo_path}")
    
    print(f"\n📋 Next steps:")
    print(f"1. Go to: {github_repo_path}")
    print(f"2. Run: git add .")
    print(f"3. Run: git commit -m 'Add AI Code Reviewer Bot files'")
    print(f"4. Run: git push origin main")
    print(f"5. Deploy to Vercel!")
    
    return True

def main():
    """Main function."""
    try:
        return copy_files_to_github_repo()
    except KeyboardInterrupt:
        print("\n\n❌ Copy cancelled by user")
        return False
    except Exception as e:
        print(f"\n❌ Copy failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Copy completed successfully!")
    else:
        print("\n❌ Copy failed. Please check the errors above.")
