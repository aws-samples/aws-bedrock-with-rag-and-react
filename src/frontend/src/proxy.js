// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT-0

// Use localhost for local development
// Make sure this matches the port your Flask server is running on
const proxy_url = "http://localhost:8000";

// Log the proxy URL for debugging
console.log("Backend API URL:", proxy_url);

export default proxy_url;