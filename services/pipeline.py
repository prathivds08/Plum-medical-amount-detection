"""
End-to-End Pipeline Orchestration Service.
Connects OCR -> Numeric Normalization -> Context Classification -> Final Provenance Assembly,
enforcing guardrails for noisy or invalid inputs.
"""
from typing import Dict, Any, Optional, Tuple, Union

from services.ocr_engine import (
    extract_text_from_image,
    detect_currency_hint,
    extract_raw_tokens,
    calculate_step1_confidence,
)
from services.digit_corrector import normalize_numeric_tokens
from services.context_classifier import classify_amounts_by_context
from services.provenance import build_step4_final_output, validate_financial_math


class MedicalAmountPipeline:
    """Orchestrator for the 4-step amount detection pipeline."""

    @staticmethod
    def run_step1(text: str, base_ocr_conf: float = 0.74) -> Dict[str, Any]:
        """
        Executes Step 1: Token extraction and guardrail validation.
        """
        raw_tokens = extract_raw_tokens(text)
        currency_hint = detect_currency_hint(text)

        # Guardrail check: if no numeric tokens could be extracted or text is trivial noise
        if not raw_tokens:
            return {
                "guardrail_triggered": True,
                "response": {
                    "status": "no_amounts_found",
                    "reason": "document too noisy"
                }
            }

        confidence = calculate_step1_confidence(raw_tokens, base_ocr_conf=base_ocr_conf)

        return {
            "guardrail_triggered": False,
            "response": {
                "raw_tokens": raw_tokens,
                "currency_hint": currency_hint,
                "confidence": confidence
            }
        }

    @staticmethod
    def run_step2(raw_tokens: list) -> Dict[str, Any]:
        """
        Executes Step 2: Normalization and digit correction.
        """
        normalized_amounts, norm_conf = normalize_numeric_tokens(raw_tokens)
        return {
            "normalized_amounts": normalized_amounts,
            "normalization_confidence": norm_conf
        }

    @staticmethod
    def run_step3(normalized_amounts: list, context_text: str) -> Dict[str, Any]:
        """
        Executes Step 3: Classification by surrounding context.
        """
        classified, class_conf = classify_amounts_by_context(normalized_amounts, context_text)
        return {
            "amounts": classified,
            "confidence": class_conf
        }

    @staticmethod
    def run_step4(classified_amounts: list, currency: str, context_text: str) -> Dict[str, Any]:
        """
        Executes Step 4: Final output formatting with source provenance.
        """
        return build_step4_final_output(classified_amounts, currency, context_text)

    @classmethod
    def process_text(cls, text: str) -> Dict[str, Any]:
        """
        Executes full end-to-end pipeline from text input.
        """
        # Step 1
        s1 = cls.run_step1(text, base_ocr_conf=0.74)
        if s1["guardrail_triggered"]:
            return {
                "input_text": text,
                "step1": s1["response"],
                "step2": None,
                "step3": None,
                "step4": s1["response"],
                "math_validation": None
            }

        s1_res = s1["response"]
        raw_tokens = s1_res["raw_tokens"]
        currency = s1_res.get("currency_hint") or "INR"

        # Step 2
        s2_res = cls.run_step2(raw_tokens)
        normalized_amounts = s2_res["normalized_amounts"]

        if not normalized_amounts:
            guardrail = {
                "status": "no_amounts_found",
                "reason": "document too noisy"
            }
            return {
                "input_text": text,
                "step1": s1_res,
                "step2": s2_res,
                "step3": None,
                "step4": guardrail,
                "math_validation": None
            }

        # Step 3
        s3_res = cls.run_step3(normalized_amounts, text)
        classified_amounts = s3_res["amounts"]

        # Step 4
        s4_res = cls.run_step4(classified_amounts, currency, text)
        math_check = validate_financial_math(classified_amounts)

        return {
            "input_text": text,
            "step1": s1_res,
            "step2": s2_res,
            "step3": s3_res,
            "step4": s4_res,
            "math_validation": math_check
        }

    @classmethod
    def process_image(cls, image_bytes: bytes) -> Dict[str, Any]:
        """
        Executes full end-to-end pipeline from raw image bytes.
        """
        ocr_text, ocr_conf = extract_text_from_image(image_bytes)
        
        # If OCR returned nothing, trigger guardrail
        if not ocr_text or not ocr_text.strip():
            guardrail = {
                "status": "no_amounts_found",
                "reason": "document too noisy"
            }
            return {
                "input_text": "",
                "step1": guardrail,
                "step2": None,
                "step3": None,
                "step4": guardrail,
                "math_validation": None
            }

        # Run pipeline with OCR base confidence
        s1 = cls.run_step1(ocr_text, base_ocr_conf=ocr_conf)
        if s1["guardrail_triggered"]:
            return {
                "input_text": ocr_text,
                "step1": s1["response"],
                "step2": None,
                "step3": None,
                "step4": s1["response"],
                "math_validation": None
            }

        s1_res = s1["response"]
        raw_tokens = s1_res["raw_tokens"]
        currency = s1_res.get("currency_hint") or "INR"

        s2_res = cls.run_step2(raw_tokens)
        normalized_amounts = s2_res["normalized_amounts"]

        if not normalized_amounts:
            guardrail = {
                "status": "no_amounts_found",
                "reason": "document too noisy"
            }
            return {
                "input_text": ocr_text,
                "step1": s1_res,
                "step2": s2_res,
                "step3": None,
                "step4": guardrail,
                "math_validation": None
            }

        s3_res = cls.run_step3(normalized_amounts, ocr_text)
        classified_amounts = s3_res["amounts"]

        s4_res = cls.run_step4(classified_amounts, currency, ocr_text)
        math_check = validate_financial_math(classified_amounts)

        return {
            "input_text": ocr_text,
            "step1": s1_res,
            "step2": s2_res,
            "step3": s3_res,
            "step4": s4_res,
            "math_validation": math_check
        }
