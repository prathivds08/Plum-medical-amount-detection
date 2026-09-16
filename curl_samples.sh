#!/bin/bash
# Sample cURL commands for testing Plum Problem Statement 4 API

BASE_URL="http://localhost:8000"

echo "=== 1. Health Check ==="
curl -s -X GET "$BASE_URL/api/v1/health" | jq .
echo -e "\n"

echo "=== 2. Step 1: OCR / Text Extraction ==="
curl -s -X POST "$BASE_URL/api/v1/step1-extract" \
  -H "Content-Type: application/json" \
  -d '{"text": "Total: INR 1200 | Paid: 1000 | Due: 200 | Discount: 10%"}' | jq .
echo -e "\n"

echo "=== 3. Step 2: Numeric Normalization & Digit Error Correction ==="
curl -s -X POST "$BASE_URL/api/v1/step2-normalize" \
  -H "Content-Type: application/json" \
  -d '{"raw_tokens": ["l200", "1000", "200", "10%"], "currency_hint": "INR"}' | jq .
echo -e "\n"

echo "=== 4. Step 3: Classification by Context ==="
curl -s -X POST "$BASE_URL/api/v1/step3-classify" \
  -H "Content-Type: application/json" \
  -d '{"normalized_amounts": [1200, 1000, 200], "text": "Total: INR 1200 | Paid: 1000 | Due: 200"}' | jq .
echo -e "\n"

echo "=== 5. Step 4: Final Output with Provenance ==="
curl -s -X POST "$BASE_URL/api/v1/step4-final" \
  -H "Content-Type: application/json" \
  -d '{"amounts": [{"type": "total_bill", "value": 1200}, {"type": "paid", "value": 1000}, {"type": "due", "value": 200}], "currency": "INR", "text": "Total: INR 1200 | Paid: 1000 | Due: 200"}' | jq .
echo -e "\n"

echo "=== 6. Universal End-to-End (PDF Sample 1: Typed Text) ==="
curl -s -X POST "$BASE_URL/api/v1/process" \
  -H "Content-Type: application/json" \
  -d '{"text": "Total: INR 1200 | Paid: 1000 | Due: 200 | Discount: 10%"}' | jq .
echo -e "\n"

echo "=== 7. Universal End-to-End (PDF Sample 2: OCR Noise & Typos) ==="
curl -s -X POST "$BASE_URL/api/v1/process" \
  -H "Content-Type: application/json" \
  -d '{"text": "T0tal: Rs l200 | Pald: 1000 | Due: 200"}' | jq .
echo -e "\n"

echo "=== 8. Universal End-to-End (Guardrail Exit: Unreadable Noise) ==="
curl -s -X POST "$BASE_URL/api/v1/process" \
  -H "Content-Type: application/json" \
  -d '{"text": "### ??? [unreadable crumpled paper artifacts - no numbers here] ~~~"}' | jq .
echo -e "\n"

echo "=== 9. Universal End-to-End (Image Upload) ==="
curl -s -X POST "$BASE_URL/api/v1/process-image" \
  -F "file=@sample_data/sample_receipt_clean.png" | jq .
echo -e "\n"
