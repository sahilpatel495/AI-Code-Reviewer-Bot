"""
Complete upload script to ensure all files are properly uploaded to GitHub
"""

import os
import shutil
from pathlib import Path

def create_complete_upload():
    """Create a complete upload package with all files."""
    
    print("📦 Creating complete upload package...")
    print("=" * 50)
    
    # Create upload directory
    upload_dir = Path("complete-upload")
    if upload_dir.exists():
        shutil.rmtree(upload_dir)
    upload_dir.mkdir()
    
    # Get current directory
    current_dir = Path.cwd()
    print(f"📁 Source directory: {current_dir}")
    
    # List all files and directories to copy
    items_to_copy = []
    
    # Add all Python files
    for py_file in current_dir.glob("*.py"):
        items_to_copy.append(py_file.name)
    
    # Add all configuration files
    for config_file in current_dir.glob("*.*"):
        if config_file.suffix in ['.txt', '.json', '.yml', '.yaml', '.md', '.sh', '.example']:
            items_to_copy.append(config_file.name)
    
    # Add all directories
    for dir_item in current_dir.iterdir():
        if dir_item.is_dir() and not dir_item.name.startswith('.') and dir_item.name not in ['complete-upload', 'github-upload', 'logs', 'tmp', '__pycache__']:
            items_to_copy.append(dir_item.name)
    
    print(f"📋 Found {len(items_to_copy)} items to copy:")
    for item in sorted(items_to_copy):
        print(f"   - {item}")
    
    # Copy all items
    copied_items = []
    failed_items = []
    
    for item_name in items_to_copy:
        source = current_dir / item_name
        destination = upload_dir / item_name
        
        try:
            if source.is_file():
                # Copy file
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                copied_items.append(item_name)
                print(f"✅ Copied file: {item_name}")
            elif source.is_dir():
                # Copy directory
                shutil.copytree(source, destination)
                copied_items.append(item_name)
                print(f"✅ Copied directory: {item_name}/")
            else:
                failed_items.append(item_name)
                print(f"⚠️  Skipped: {item_name} (not found)")
        except Exception as e:
            print(f"❌ Failed to copy {item_name}: {e}")
            failed_items.append(item_name)
    
    # Create a summary file
    summary_file = upload_dir / "UPLOAD_SUMMARY.txt"
    with open(summary_file, 'w') as f:
        f.write("AI Code Reviewer Bot - Upload Summary\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total items: {len(items_to_copy)}\n")
        f.write(f"Successfully copied: {len(copied_items)}\n")
        f.write(f"Failed: {len(failed_items)}\n\n")
        
        f.write("Copied items:\n")
        for item in sorted(copied_items):
            f.write(f"  ✅ {item}\n")
        
        if failed_items:
            f.write("\nFailed items:\n")
            for item in sorted(failed_items):
                f.write(f"  ❌ {item}\n")
        
        f.write("\n" + "=" * 50 + "\n")
        f.write("Upload Instructions:\n")
        f.write("1. Go to: https://github.com/sahilpatel495/AI-Code-Reviewer-Bot\n")
        f.write("2. Click 'uploading an existing file'\n")
        f.write("3. Drag and drop ALL files from this directory\n")
        f.write("4. Add commit message: 'Complete upload: All AI Code Reviewer Bot files'\n")
        f.write("5. Click 'Commit changes'\n")
        f.write("6. Deploy to Vercel!\n")
    
    print(f"\n📊 Upload Summary:")
    print(f"   ✅ Successfully copied: {len(copied_items)} items")
    print(f"   ❌ Failed: {len(failed_items)} items")
    
    if failed_items:
        print(f"\n⚠️  Failed items: {', '.join(failed_items)}")
    
    print(f"\n🎉 Complete upload package created!")
    print(f"📁 Upload directory: {upload_dir.absolute()}")
    print(f"📄 Summary file: {summary_file.absolute()}")
    
    print(f"\n📋 Next steps:")
    print(f"1. Go to: https://github.com/sahilpatel495/AI-Code-Reviewer-Bot")
    print(f"2. Click 'uploading an existing file'")
    print(f"3. Drag and drop ALL files from: {upload_dir.absolute()}")
    print(f"4. Add commit message: 'Complete upload: All AI Code Reviewer Bot files'")
    print(f"5. Click 'Commit changes'")
    print(f"6. Deploy to Vercel!")
    
    return True

if __name__ == "__main__":
    try:
        create_complete_upload()
        print("\n✅ Complete upload package created successfully!")
    except Exception as e:
        print(f"\n❌ Failed to create upload package: {e}")
