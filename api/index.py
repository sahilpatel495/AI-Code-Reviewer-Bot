"""
Vercel serverless function entry point for AI Code Reviewer Bot
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the FastAPI app
from app import app

# Export the app for Vercel
handler = app
