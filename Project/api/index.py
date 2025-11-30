# Vercel serverless function entry point
# This file imports and exposes the Flask app for Vercel

import sys
import os

# Add the src directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
src_path = os.path.join(project_root, 'src')
sys.path.insert(0, src_path)

# Change working directory to src so templates/static are found
os.chdir(src_path)

# Import the Flask app
from app import app

# Vercel looks for 'app' or 'handler'
handler = app
