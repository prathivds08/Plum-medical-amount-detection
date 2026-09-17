# AI-Powered Amount Detection in Medical Documents
> **Plum Internship Technical Assignment &bull; Problem Statement 4**
> Focus Area: OCR &rarr; Numeric Normalization &rarr; Context Classification &rarr; Provenance Extraction

---

## 📌 Executive Summary

This repository contains a production-grade backend service and modern SaaS web application that extracts financial amounts from typed or scanned medical bills and receipts (including crumpled, noisy, or degraded inputs). The system handles OCR errors, digit confusions, percentage exclusions, context classification, mathematical consistency validation, and produces structured JSON outputs with exact textual provenance and guardrails.

---

## 🏗️ Architecture & Pipeline Overview

```
[ Input: Raw Text or Scanned Bill Image ]
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│ Step 1: OCR / Text Extraction                          │
│ - Image preprocessing (grayscale, CLAHE, denoising)    │
│ - RapidOCR engine extraction                           │
│ - Numeric, percentage & currency token discovery       │
│ - Guardrail Exit: "no_amounts_found" (noisy document) │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│ Step 2: Numeric Normalization & Digit Correction       │
│ - OCR character confusion matrix (l/I/| -> 1, O/o -> 0)│
│ - Filter non-monetary rates (e.g., '10%' discount)     │
│ - Type casting to integers / floats                    │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│ Step 3: Context Classification                         │
│ - Word-boundary sliding window context extractor       │
│ - Fuzzy matching for OCR typos ('T0tal', 'Pald')       │
│ - Semantic labels: total_bill, paid, due, discount     │
└───────────────────┬────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│ Step 4: Final JSON Output & Provenance Tracking        │
│ - Trace exact original substring: "text: '...'"        │
│ - Inferred ISO Currency (INR, USD, EUR, etc.)          │
│ - Mathematical balance audit: Total == Paid + Due      │
│ - Strict adherence to assignment JSON schema           │
└────────────────────────────────────────────────────────┘
```

---

## 🎯 JSON Schema Adherence (As Specified in Assignment)

### Step 1 — OCR / Text Extraction
**Input (Typed Text):**
```text
Total: INR 1200 | Paid: 1000 | Due: 200 | Discount: 10%
```
**Input (OCR Sample with Typos):**
```text
T0tal: Rs l200 | Pald: 1000 | Due: 200
```
**Expected Output:**
```json
{
  "raw_tokens": ["1200", "1000", "200", "10%"],
  "currency_hint": "INR",
  "confidence": 0.74
}
```
**Guardrail / Exit Condition:**
```json
{
  "status": "no_amounts_found",
  "reason": "document too noisy"
}
```

### Step 2 — Normalization
Fixes OCR digit errors (`l200` &rarr; `1200`), strips discount percentages, and maps to clean numbers:
```json
{
  "normalized_amounts": [1200, 1000, 200],
  "normalization_confidence": 0.82
}
```

### Step 3 — Classification by Context
Uses surrounding text to label amounts:
```json
{
  "amounts": [
    {"type": "total_bill", "value": 1200},
    {"type": "paid", "value": 1000},
    {"type": "due", "value": 200}
  ],
  "confidence": 0.80
}
```

### Step 4 — Final Output with Provenance
Combines labeled amounts, ISO currency, and textual lineage:
```json
{
  "currency": "INR",
  "amounts": [
    {"type": "total_bill", "value": 1200, "source": "text: 'Total: INR 1200'"},
    {"type": "paid", "value": 1000, "source": "text: 'Paid: 1000'"},
    {"type": "due", "value": 200, "source": "text: 'Due: 200'"}
  ],
  "status": "ok"
}
```

---

## 📂 Project Structure

```
Plum-medical-amount-detection/
├── main.py                  # FastAPI server entrypoint & route handlers
├── models.py                # Pydantic schemas adhering to assignment requirements
├── config.py                # Environment and pipeline configurations
├── requirements.txt         # Production & testing dependencies
├── pytest.ini              # Pytest configuration & warning filters
├── curl_samples.bat         # Automated cURL test script for Windows
├── curl_samples.sh          # Automated cURL test script for Linux/macOS
├── postman_collection.json  # Complete Postman collection for all endpoints
├── services/
│   ├── __init__.py
│   ├── pipeline.py          # Master pipeline orchestrating Steps 1 to 4
│   ├── ocr_engine.py        # Step 1: RapidOCR & image preprocessing
│   ├── normalizer.py        # Step 2: OCR confusion matrix & rate filtering
│   ├── classifier.py        # Step 3: Context extraction & fuzzy keyword matching
│   └── provenance.py        # Step 4: Lineage tracking & math consistency checks
├── static/
│   ├── index.html           # Interactive web UI dashboard
│   ├── style.css            # Dark mode UI styling
│   └── app.js               # Frontend JavaScript client
├── sample_data/
│   ├── generate_samples.py  # Synthetic bill/receipt generator script
│   ├── sample_receipt_clean.png
│   ├── sample_receipt_ocr_noise.png
│   └── sample_unreadable.png
└── tests/
    ├── __init__.py
    └── test_pipeline.py     # 17 automated tests for all steps, guardrails & APIs
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.13)
- `pip` package manager

### 2. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/prathivds08/Plum-medical-amount-detection.git
cd Plum-medical-amount-detection

# Create and activate virtual environment (optional)
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Generate Sample Data
Generate synthetic clean, crumpled/noisy, and unreadable receipts:
```bash
python sample_data/generate_samples.py
```

### 4. Run the Server
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
The server will start at:
- **Interactive SaaS Web Application**: [http://localhost:8000/](http://localhost:8000/)
  - Document drag-and-drop (PDF, PNG, JPG) with live preview thumbnail
  - One-click sample presets (`Clean PDF`, `Noisy OCR Typos`, `Hospital Bill`, `Scanned Receipt`, `Unreadable Noise`)
  - Multi-step progress animation explaining OCR and classification in real time
  - Prominent Bill Summary cards (Total Bill, Amount Paid, Amount Due) with currency formatting
  - Plain-English mathematical audit banner (`Total == Paid + Due`)
  - AI Confidence meter with advisory microcopy
  - Non-technical 4-step analysis timeline
  - Collapsible developer accordion with exact document provenance tracing and formatted JSON
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🌐 Live Demo with Ngrok

To share a live working public URL for evaluators:
```bash
# In a separate terminal
ngrok http 8000
```
This gives a public URL (e.g. `https://xxxx.ngrok-free.app`) where both the Web Dashboard and REST API endpoints are instantly accessible worldwide.

---

## 🧪 Running Automated Tests

Run the full automated test suite with pytest:
```bash
pytest -v
```
**Test Coverage Includes:**
- Step 1 token and currency extraction from text and OCR samples
- Step 1 guardrail trigger on unreadable/noisy inputs
- Step 2 OCR digit confusion correction (`l200` &rarr; `1200`, `1OOO` &rarr; `1000`)
- Step 2 exclusion of percentage tokens (`10%`)
- Step 3 context classification with clean and corrupted labels (`T0tal`, `Pald`)
- Step 4 exact source snippet provenance formatting
- Arithmetic consistency audit (`Total == Paid + Due`)
- End-to-end REST API integration tests for text and image multipart uploads

### Quick Test via cURL Scripts

Run all endpoints sequentially against a running local server:
- **Windows (PowerShell or Command Prompt)**:
  ```powershell
  .\curl_samples.bat
  ```
- **Linux / macOS**:
  ```bash
  chmod +x curl_samples.sh
  ./curl_samples.sh
  ```

---

## 📡 API Endpoints Reference

### 1. End-to-End Processing (Text)
- **Endpoint**: `POST /api/v1/process`
- **Request Body**:
```bash
curl -X POST "http://localhost:8000/api/v1/process" \
  -H "Content-Type: application/json" \
  -d '{"text": "Total: INR 1200 | Paid: 1000 | Due: 200 | Discount: 10%"}'
```

### 2. End-to-End Processing (Image Upload)
- **Endpoint**: `POST /api/v1/process-image`
```bash
curl -X POST "http://localhost:8000/api/v1/process-image" \
  -F "file=@sample_data/sample_receipt_clean.png"
```

### 3. Step 1: OCR / Text Extraction
- **Endpoint**: `POST /api/v1/step1-extract`
```bash
curl -X POST "http://localhost:8000/api/v1/step1-extract" \
  -H "Content-Type: application/json" \
  -d '{"text": "T0tal: Rs l200 | Pald: 1000 | Due: 200"}'
```

### 4. Step 2: Numeric Normalization
- **Endpoint**: `POST /api/v1/step2-normalize`
```bash
curl -X POST "http://localhost:8000/api/v1/step2-normalize" \
  -H "Content-Type: application/json" \
  -d '{"raw_tokens": ["l200", "1000", "200", "10%"]}'
```

### 5. Step 3: Context Classification
- **Endpoint**: `POST /api/v1/step3-classify`
```bash
curl -X POST "http://localhost:8000/api/v1/step3-classify" \
  -H "Content-Type: application/json" \
  -d '{"normalized_amounts": [1200, 1000, 200], "text": "Total: INR 1200 | Paid: 1000 | Due: 200"}'
```

### 6. Step 4: Final Output with Provenance
- **Endpoint**: `POST /api/v1/step4-final`
```bash
curl -X POST "http://localhost:8000/api/v1/step4-final" \
  -H "Content-Type: application/json" \
  -d '{"amounts": [{"type": "total_bill", "value": 1200}, {"type": "paid", "value": 1000}, {"type": "due", "value": 200}], "currency": "INR", "text": "Total: INR 1200 | Paid: 1000 | Due: 200"}'
```

---

## 📁 Postman Collection

Import `postman_collection.json` into Postman to test all endpoints out-of-the-box with pre-configured requests and environments.

---

## 🎥 Screen Recording Demo Script

When recording your 2-3 minute demo video for submission:
1. **Introduction (15s)**:
   - Briefly introduce Problem Statement 4 (AI-Powered Amount Detection in Medical Documents).
   - Highlight the end-to-end architecture: OCR &rarr; Numeric Normalization &rarr; Context Classification &rarr; Mathematical Audit &rarr; Provenance.
2. **Interactive SaaS UI Demo (60s)**:
   - Open `http://localhost:8000`.
   - Point out the clean consumer-grade layout (Document Input on the left, Bill Summary & Analysis on the right).
   - Click **"Clean PDF"** preset &rarr; click **"Analyze Bill"** &rarr; point out the 4-step progress animation, the high AI Confidence, the prominent cards (**Total Bill: ₹1,200**, **Amount Paid: ₹1,000**, **Amount Due: ₹200**), and the balanced mathematical audit banner.
   - Click **"Noisy OCR Typos"** preset &rarr; hit **"Analyze Bill"** &rarr; show how `l200` is corrected to `1200` and `T0tal`/`Pald` are classified accurately.
   - Click **"Hospital Bill"** preset &rarr; show how additional itemized fees (*Consultation Fee*, *Medicines*, *Lab Work*) are cleanly extracted into secondary chips.
   - Click **"Scanned Receipt"** preset &rarr; show the live document image preview and OCR processing in action.
   - Click **"Unreadable Noise"** preset &rarr; demonstrate the friendly guardrail exit condition: *"We couldn't confidently identify financial amounts (reason: document too noisy)"*.
   - Expand **"View technical details & provenance"** &rarr; show evaluators the exact document provenance tracing strings (`text: 'Total: INR 1200'`), raw vs. normalized tokens, and the assignment-compliant JSON output with 1-click copy.
3. **Swagger API / Terminal Demo (20s)**:
   - Show `http://localhost:8000/docs` or run `./curl_samples.sh` / `.\curl_samples.bat`.
4. **Codebase & Tests (25s)**:
   - Run `pytest -v` in the terminal to show all 17 unit and integration tests passing in ~2.5 seconds.
   - Briefly highlight the modular architecture under `services/` (`ocr_engine.py`, `normalizer.py`, `classifier.py`, `provenance.py`).
