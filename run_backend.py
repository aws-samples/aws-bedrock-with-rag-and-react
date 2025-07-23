#!/usr/bin/env python3
import os
import sys
import subprocess

# Print Python version and path
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Try to import Flask
try:
    import flask
    print(f"Flask version: {flask.__version__}")
except ImportError:
    print("Flask is not installed. Please install it with:")
    print(f"{sys.executable} -m pip install flask flask-cors")
    sys.exit(1)

# Run the minimal Flask app
try:
    print("Starting minimal Flask server on port 8000...")
    os.chdir('src/backend')
    from app_py_new import app
    app.run(host='0.0.0.0', port=8000, debug=True)
except Exception as e:
    print(f"Error running minimal Flask app: {e}")
    sys.exit(1)