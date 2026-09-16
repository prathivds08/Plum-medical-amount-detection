"""
Comprehensive Automated Test Suite for Problem Statement 4.
Validates Steps 1-4, OCR corrections, Guardrails, Schema Adherence, and REST APIs.
"""
import os
import pytest
from fastapi.testclient import TestClient

from main import app
from services.ocr_engine import extract_raw_tokens, detect_currency_hint
from services.digit_corrector import normalize_numeric_tokens, correct_ocr_digits
from services.context_classifier import classify_amounts_by_context
from services.provenance import extract_provenance_source, validate_financial_math
from services.pipeline import MedicalAmountPipeline

client = TestClient(app)

SAMPLE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_data")


# -------------------------------------------------------------
# Unit Tests for Step 1: Token & Currency Extraction & Guardrails
# -------------------------------------------------------------

def test_step1_typed_text_extraction():
    """Validates token extraction on typed text from the PDF."""
    text = "Total: INR 1200 | Paid: 1000 | Due: 200 | Discount: 10%"
    tokens = extract_raw_tokens(text)
    currency = detect_currency_hint(text)

    assert "1200" in tokens
    assert "1000" in tokens
    assert "200" in tokens
    assert "10%" in tokens
    assert currency == "INR"

    s1_res = MedicalAmountPipeline.run_step1(text)
    assert not s1_res["guardrail_triggered"]
    assert s1_res["response"]["raw_tokens"] == ["1200", "1000", "200", "10%"]
    assert s1_res["response"]["currency_hint"] == "INR"
    assert s1_res["response"]["confidence"] >= 0.70


def test_step1_ocr_noisy_tokens():
    """Validates token extraction on OCR text sample from the PDF."""
    ocr_sample = "T0tal: Rs l200 | Pald: 1000 | Due: 200"
    tokens = extract_raw_tokens(ocr_sample)
    currency = detect_currency_hint(ocr_sample)

    assert "l200" in tokens
    assert "1000" in tokens
    assert "200" in tokens
    assert currency == "INR"


def test_step1_guardrail_noisy_unreadable():
    """Validates guardrail trigger when document contains no valid amounts."""
    noisy_text = "### ??? [crumpled blurry paper artifacts with no numbers] ~~~"
    s1_res = MedicalAmountPipeline.run_step1(noisy_text)

    assert s1_res["guardrail_triggered"] is True
    assert s1_res["response"]["status"] == "no_amounts_found"
    assert s1_res["response"]["reason"] == "document too noisy"


# -------------------------------------------------------------
# Unit Tests for Step 2: Normalization & Digit Error Correction
# -------------------------------------------------------------

def test_step2_digit_corrector():
    """Validates OCR digit substitutions (l->1, O->0, etc.)."""
    assert correct_ocr_digits("l200") == "1200"
    assert correct_ocr_digits("1OOO") == "1000"
    assert correct_ocr_digits("l000") == "1000"


def test_step2_numeric_normalization_and_percentage_filter():
    """Validates Step 2 mapping to numbers and exclusion of discount percentage."""
    raw_tokens = ["1200", "1000", "200", "10%"]
    normalized, conf = normalize_numeric_tokens(raw_tokens)

    assert normalized == [1200, 1000, 200]
    assert 10 not in normalized  # '10%' must be excluded
    assert conf >= 0.80


def test_step2_recovers_corrupted_digits():
    """Validates Step 2 fixing 'l200' into integer 1200."""
    raw_tokens = ["l200", "1000", "200"]
    normalized, conf = normalize_numeric_tokens(raw_tokens)

    assert normalized == [1200, 1000, 200]
    assert conf >= 0.80


# -------------------------------------------------------------
# Unit Tests for Step 3: Context Classification
# -------------------------------------------------------------

def test_step3_context_classification_standard():
    """Validates classification into total_bill, paid, and due."""
    text = "Total: INR 1200 | Paid: 1000 | Due: 200 | Discount: 10%"
    normalized = [1200, 1000, 200]

    classified, conf = classify_amounts_by_context(normalized, text)

    assert len(classified) == 3
    assert classified[0] == {"type": "total_bill", "value": 1200}
    assert classified[1] == {"type": "paid", "value": 1000}
    assert classified[2] == {"type": "due", "value": 200}
    assert conf >= 0.80


def test_step3_context_classification_with_ocr_typos():
    """Validates classification when labels have OCR typos (T0tal, Pald)."""
    text = "T0tal: Rs l200 | Pald: 1000 | Due: 200"
    normalized = [1200, 1000, 200]

    classified, conf = classify_amounts_by_context(normalized, text)

    type_map = {item["value"]: item["type"] for item in classified}
    assert type_map[1200] == "total_bill"
    assert type_map[1000] == "paid"
    assert type_map[200] == "due"


# -------------------------------------------------------------
# Unit Tests for Step 4: Provenance & Math Consistency
# -------------------------------------------------------------

def test_step4_provenance_and_math():
    """Validates exact snippet provenance and mathematical check."""
    text = "Total: INR 1200 | Paid: 1000 | Due: 200"
    classified = [
        {"type": "total_bill", "value": 1200},
        {"type": "paid", "value": 1000},
        {"type": "due", "value": 200}
    ]

    p1 = extract_provenance_source(1200, text)
    assert "Total" in p1 and "1200" in p1

    math_result = validate_financial_math(classified)
    assert math_result["is_balanced"] is True
    assert math_result["equation"] == "1200 == 1000 + 200"

    final_output = MedicalAmountPipeline.run_step4(classified, "INR", text)
    assert final_output["currency"] == "INR"
    assert final_output["status"] == "ok"
    assert len(final_output["amounts"]) == 3
    assert final_output["amounts"][0]["source"].startswith("text:")


# -------------------------------------------------------------
# Integration Tests via FastAPI REST Endpoints
# -------------------------------------------------------------

def test_api_health():
    """Tests /api/v1/health."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_api_step1_extract_endpoint():
    """Tests /api/v1/step1-extract with text."""
    res = client.post("/api/v1/step1-extract", json={"text": "Total: INR 1200 | Paid: 1000 | Due: 200 | Discount: 10%"})
    assert res.status_code == 200
    data = res.json()
    assert "raw_tokens" in data
    assert data["currency_hint"] == "INR"


def test_api_step2_normalize_endpoint():
    """Tests /api/v1/step2-normalize directly."""
    res = client.post("/api/v1/step2-normalize", json={"raw_tokens": ["l200", "1000", "200", "10%"]})
    assert res.status_code == 200
    data = res.json()
    assert data["normalized_amounts"] == [1200, 1000, 200]
    assert data["normalization_confidence"] >= 0.80


def test_api_step3_classify_endpoint():
    """Tests /api/v1/step3-classify directly."""
    res = client.post("/api/v1/step3-classify", json={
        "normalized_amounts": [1200, 1000, 200],
        "text": "Total: INR 1200 | Paid: 1000 | Due: 200"
    })
    assert res.status_code == 200
    data = res.json()
    assert len(data["amounts"]) == 3
    assert data["amounts"][0]["type"] == "total_bill"


def test_api_step4_final_endpoint():
    """Tests /api/v1/step4-final directly."""
    res = client.post("/api/v1/step4-final", json={
        "amounts": [{"type": "total_bill", "value": 1200}, {"type": "paid", "value": 1000}, {"type": "due", "value": 200}],
        "currency": "INR",
        "text": "Total: INR 1200 | Paid: 1000 | Due: 200"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["currency"] == "INR"
    assert data["status"] == "ok"
    assert data["amounts"][0]["source"] == "text: 'Total: INR 1200'"


def test_api_universal_process_text():
    """Tests full pipeline text processor /api/v1/process."""
    payload = {"text": "Total: INR 1200 | Paid: 1000 | Due: 200 | Discount: 10%"}
    res = client.post("/api/v1/process", json=payload)
    assert res.status_code == 200
    data = res.json()

    assert data["step1"]["raw_tokens"] == ["1200", "1000", "200", "10%"]
    assert data["step2"]["normalized_amounts"] == [1200, 1000, 200]
    assert len(data["step3"]["amounts"]) == 3
    assert data["step4"]["status"] == "ok"
    assert data["step4"]["currency"] == "INR"
    assert data["math_validation"]["is_balanced"] is True


def test_api_universal_process_guardrail():
    """Tests full pipeline guardrail on noisy input."""
    payload = {"text": "@@@ ???? *** blurry no amounts here"}
    res = client.post("/api/v1/process", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["step1"]["status"] == "no_amounts_found"
    assert data["step4"]["status"] == "no_amounts_found"


def test_api_process_image_upload():
    """Tests image upload endpoint /api/v1/process-image with clean receipt."""
    clean_img_path = os.path.join(SAMPLE_DIR, "sample_receipt_clean.png")
    if os.path.exists(clean_img_path):
        with open(clean_img_path, "rb") as f:
            res = client.post("/api/v1/process-image", files={"file": ("receipt.png", f, "image/png")})
        assert res.status_code == 200
        data = res.json()
        assert data["step4"]["status"] == "ok"
        assert len(data["step4"]["amounts"]) >= 2
