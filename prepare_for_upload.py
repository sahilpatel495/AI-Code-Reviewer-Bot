"""
Script to prepare files for GitHub upload
"""

import os
import shutil
from pathlib import Path

def prepare_files_for_upload():
    """Prepare all files for GitHub upload."""
    
    print("📦 Preparing files for GitHub upload...")
    print("=" * 50)
    
    # Create upload directory
    upload_dir = Path("github-upload")
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
    upload_dir.mkdir()
    
    # List of files to include
    files_to_include = [
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
        'copy_to_github.py',
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
    
    for file_path in files_to_include:
        source = Path(file_path)
        destination = upload_dir / file_path
        
        try:
            if source.is_file():
                # Copy file
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                copied_files.append(file_path)
                print(f"✅ Prepared: {file_path}")
            elif source.is_dir():
                # Copy directory
                shutil.copytree(source, destination)
                copied_files.append(file_path)
                print(f"✅ Prepared: {file_path}/")
            else:
                skipped_files.append(file_path)
                print(f"⚠️  Skipped: {file_path} (not found)")
        except Exception as e:
            print(f"❌ Failed to prepare {file_path}: {e}")
            skipped_files.append(file_path)
    
    print(f"\n📊 Preparation Summary:")
    print(f"   ✅ Prepared: {len(copied_files)} items")
    print(f"   ⚠️  Skipped: {len(skipped_files)} items")
    
    if skipped_files:
        print(f"\n⚠️  Skipped files: {', '.join(skipped_files)}")
    
    print(f"\n🎉 Files prepared successfully!")
    print(f"📁 Upload directory: {upload_dir.absolute()}")
    
    print(f"\n📋 Next steps:")
    print(f"1. Go to: https://github.com/sahilpatel495/AI-Code-Reviewer-Bot")
    print(f"2. Click 'uploading an existing file'")
    print(f"3. Drag and drop all files from: {upload_dir.absolute()}")
    print(f"4. Add commit message: 'Initial commit: AI Code Reviewer Bot'")
    print(f"5. Click 'Commit changes'")
    print(f"6. Deploy to Vercel!")
    
    return True

if __name__ == "__main__":
    try:
        prepare_files_for_upload()
        print("\n✅ Preparation completed successfully!")
    except Exception as e:
        print(f"\n❌ Preparation failed: {e}")
