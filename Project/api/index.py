# Vercel serverless function entry point
# This file imports and exposes the Flask app for Vercel

import sys
import os

# Add the src directory to the Python path
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src')
sys.path.insert(0, src_path)

# Import the Flask app
from app import app

# Vercel looks for 'app' or 'handler'
handler = app
