#!/usr/bin/env python3
import requests
import json
import sys

# Get the question from command line arguments or use a default
question = sys.argv[1] if len(sys.argv) > 1 else "what is panoptic"

print(f"Testing question: '{question}'")

# Prepare the payload
payload = {
    "body": json.dumps({
        "prompt": question
    })
}

# Send the request to the server
try:
    response = requests.post(
        "http://localhost:8000/api/conversation/predict-claude",
        json=payload
    )
    
    # Print the response
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        print("Response:")
        print(response.json())
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error sending request: {e}")