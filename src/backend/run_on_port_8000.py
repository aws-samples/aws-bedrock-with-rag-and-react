#!/usr/bin/env python3
import sys
import os

# Print Python version and path for debugging
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Try to import Flask
try:
    import flask
    print(f"Flask version: {flask.__version__}")
except ImportError:
    print("Flask is not installed. Please install it with: pip install flask flask-cors")
    sys.exit(1)

# Try to import other required modules
try:
    import boto3
    import langchain
    print("Required modules imported successfully")
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install all required dependencies with: pip install -r requirements.txt")
    sys.exit(1)

try:
    # Import the app
    from app import app
    
    # Run the Flask app
    if __name__ == "__main__":
        print("Starting Flask server on port 8000...")
        print("API will be available at http://localhost:8000")
        print("Press Ctrl+C to stop the server")
        app.run(host='0.0.0.0', port=8000, debug=True)
except Exception as e:
    print(f"Error starting Flask server: {e}")
    sys.exit(1)