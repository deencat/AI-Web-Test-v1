#!/bin/bash
# Manual Test Script for Loop Execution Enhancement
# This script creates a test case with loop blocks and executes it

echo "=========================================="
echo "Loop Execution Manual Test"
echo "=========================================="
echo ""

# Activate virtual environment
source /home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend/venv/bin/activate

# Get authentication token (you'll need to login first if not already logged in)
# For testing, we'll use a placeholder - replace with actual token
TOKEN="your_token_here"

echo "Step 1: Creating test case with loop blocks..."
echo ""

# Create test case with loop blocks via API
curl -X POST http://localhost:8000/api/v1/tests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
  "title": "Manual Test: Upload 3 HKID Documents (Loop)",
  "description": "Test loop execution with 3 file upload iterations",
  "test_type": "e2e",
  "priority": "high",
  "steps": [
    "Navigate to document upload page",
    "Click upload button",
    "Select file from dialog",
    "Click confirm button",
    "Verify all documents uploaded successfully"
  ],
  "expected_result": "All 3 documents uploaded successfully",
  "preconditions": "User is logged in and has access to upload page",
  "test_data": {
    "detailed_steps": [
      {
        "action": "navigate",
        "value": "http://localhost:3000/upload"
      },
      {
        "action": "click",
        "selector": "#upload-btn"
      },
      {
        "action": "upload_file",
        "selector": "input[type=\"file\"]",
        "file_path": "/home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend/test_files/hkid_sample.pdf",
        "instruction": "Upload HKID document {iteration}"
      },
      {
        "action": "click",
        "selector": "#confirm-btn"
      },
      {
        "action": "verify",
        "selector": ".success-message",
        "expected": "Upload successful"
      }
    ],
    "loop_blocks": [
      {
        "id": "file_upload_loop",
        "start_step": 2,
        "end_step": 4,
        "iterations": 3,
        "description": "Upload 3 HKID documents",
        "variables": {
          "file_path": "/home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend/test_files/hkid_sample.pdf"
        }
      }
    ]
  }
}' | jq .

echo ""
echo "=========================================="
echo "Test case created!"
echo "Check the response above for the test_id"
echo ""
echo "Step 2: To execute the test, use:"
echo "curl -X POST http://localhost:8000/api/v1/executions \\\"
echo "  -H 'Authorization: Bearer \$TOKEN' \\\"
echo "  -H 'Content-Type: application/json' \\\"
echo "  -d '{\"test_case_id\": YOUR_TEST_ID}'"
echo ""
echo "Step 3: Watch backend logs for loop execution:"
echo "Look for lines containing [LOOP] in the backend terminal"
echo ""
echo "Step 4: Check screenshots folder:"
echo "ls -la /home/dt-qa/alex_workspace/AI-Web-Test-v1-main/backend/screenshots/"
echo "Look for files like: exec_*_step_*_iter_*_pass.png"
echo "=========================================="
