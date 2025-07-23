#!/usr/bin/env python3
import os
import sys
import requests

# Print Python version and path
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Test if the backend is running
try:
    print("Testing connection to backend at http://localhost:8000/api/check-vector")
    response = requests.get("http://localhost:8000/api/check-vector")
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")
except Exception as e:
    print(f"Error connecting to backend: {e}")
    
# Test if the backend is running on port 5000
try:
    print("\nTesting connection to backend at http://localhost:5000/api/check-vector")
    response = requests.get("http://localhost:5000/api/check-vector")
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.text}")
except Exception as e:
    print(f"Error connecting to backend: {e}")
    
print("\nIf both tests failed, the backend is not running or is not accessible.")
print("Please make sure the backend is running on either port 8000 or 5000.")
print("You can start the backend with:")
print("cd src/backend && python run_on_port_8000.py")
print("\nIf the backend is running but you're still getting 'Failed to fetch' errors,")
print("it might be a CORS issue. Make sure CORS is properly configured in the backend.")