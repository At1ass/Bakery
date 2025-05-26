#!/bin/bash
curl -X POST http://localhost:8001/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testorder@example.com&password=TestPassword123!" \
  | jq -r '.access_token' 