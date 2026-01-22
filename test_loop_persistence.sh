#!/bin/bash

# Quick test script to verify loop blocks are saved and persisted

echo "🔍 Testing Loop Block Persistence"
echo "================================"
echo ""

# Get auth token
echo "📝 Step 1: Login to get auth token..."
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  | jq -r '.access_token')

if [ -z "$TOKEN" ] || [ "$TOKEN" == "null" ]; then
  echo "❌ Failed to get auth token. Is the backend running?"
  exit 1
fi

echo "✅ Got auth token: ${TOKEN:0:20}..."
echo ""

# Get first test case
echo "📝 Step 2: Get first test case..."
TEST_ID=$(curl -s -X GET "http://localhost:8000/api/v1/tests" \
  -H "Authorization: Bearer $TOKEN" \
  | jq -r '.[0].id')

if [ -z "$TEST_ID" ] || [ "$TEST_ID" == "null" ]; then
  echo "❌ No test cases found. Create a test first."
  exit 1
fi

echo "✅ Found test ID: $TEST_ID"
echo ""

# Update test with loop blocks
echo "📝 Step 3: Update test with loop blocks..."
UPDATE_RESPONSE=$(curl -s -X PUT "http://localhost:8000/api/v1/tests/$TEST_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "steps": [
      "Navigate to login page",
      "Enter username",
      "Enter password",
      "Click submit",
      "Verify success"
    ],
    "test_data": {
      "loop_blocks": [
        {
          "id": "loop_test_1",
          "start_step": 2,
          "end_step": 3,
          "iterations": 5,
          "description": "Test loop: repeat steps 2-3 five times"
        }
      ]
    }
  }')

echo "✅ Update response:"
echo "$UPDATE_RESPONSE" | jq '.'
echo ""

# Verify loop blocks persisted
echo "📝 Step 4: Fetch test again to verify loop blocks persisted..."
VERIFY_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/tests/$TEST_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "✅ Test data retrieved:"
echo "$VERIFY_RESPONSE" | jq '.test_data'
echo ""

# Check if loop_blocks exist
LOOP_BLOCKS=$(echo "$VERIFY_RESPONSE" | jq '.test_data.loop_blocks')

if [ "$LOOP_BLOCKS" != "null" ] && [ ! -z "$LOOP_BLOCKS" ]; then
  echo "✅ SUCCESS! Loop blocks are persisted:"
  echo "$LOOP_BLOCKS" | jq '.'
  echo ""
  echo "🎉 Test passed! Loop blocks are being saved and retrieved correctly."
else
  echo "❌ FAILED! Loop blocks are not persisted."
  echo "Expected: loop_blocks array"
  echo "Got: $LOOP_BLOCKS"
  exit 1
fi

echo ""
echo "================================"
echo "✅ All tests passed!"
