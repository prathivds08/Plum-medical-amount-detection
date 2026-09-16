"""
Data models and JSON schemas adhering strictly to the assignment specifications.
"""
from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field


# -------------------------------------------------------------
# Input Request Models
# -------------------------------------------------------------

class TextInputRequest(BaseModel):
    """Input payload for text-based bill/receipt processing."""
    text: str = Field(..., description="Raw bill/receipt text to analyze", examples=["Total: INR 1200 | Paid: 1000 | Due: 200 | Discount: 10%"])


class Step2NormalizeRequest(BaseModel):
    """Input payload to test Step 2 normalization directly."""
    raw_tokens: List[str] = Field(..., description="Raw tokens extracted from document", examples=[["l200", "1000", "200", "10%"]])
    currency_hint: Optional[str] = Field(None, description="Optional currency hint", examples=["INR"])


class Step3ClassifyRequest(BaseModel):
    """Input payload to test Step 3 classification directly."""
    normalized_amounts: List[Union[int, float]] = Field(..., description="Normalized numeric amounts", examples=[[1200, 1000, 200]])
    text: str = Field(..., description="Context text containing surrounding labels", examples=["Total: INR 1200 | Paid: 1000 | Due: 200"])


class Step4FinalRequest(BaseModel):
    """Input payload to test Step 4 directly."""
    amounts: List[Dict[str, Any]] = Field(..., description="Classified amounts without provenance", examples=[[{"type": "total_bill", "value": 1200}, {"type": "paid", "value": 1000}, {"type": "due", "value": 200}]])
    currency: Optional[str] = Field("INR", description="Currency code", examples=["INR"])
    text: str = Field(..., description="Original context text for provenance extraction", examples=["Total: INR 1200 | Paid: 1000 | Due: 200"])


# -------------------------------------------------------------
# Step-by-Step Response Models (Strictly matching PDF Schemas)
# -------------------------------------------------------------

class GuardrailResponse(BaseModel):
    """Guardrail exit response when input is too noisy or unparseable."""
    status: str = Field("no_amounts_found", examples=["no_amounts_found"])
    reason: str = Field("document too noisy", examples=["document too noisy"])


class Step1ExtractionSuccessResponse(BaseModel):
    """Step 1: OCR/Text Extraction response schema."""
    raw_tokens: List[str] = Field(..., description="Extracted raw numeric and percentage tokens", examples=[["1200", "1000", "200", "10%"]])
    currency_hint: Optional[str] = Field(None, description="Inferred currency hint", examples=["INR"])
    confidence: float = Field(..., description="Extraction confidence score (0.0 to 1.0)", examples=[0.74])


class Step2NormalizationSuccessResponse(BaseModel):
    """Step 2: Normalization response schema."""
    normalized_amounts: List[Union[int, float]] = Field(..., description="Cleaned and validated numeric amounts", examples=[[1200, 1000, 200]])
    normalization_confidence: float = Field(..., description="Normalization confidence score (0.0 to 1.0)", examples=[0.82])


class ClassifiedAmountItem(BaseModel):
    """Individual classified amount in Step 3."""
    type: str = Field(..., description="Label such as total_bill, paid, due, discount", examples=["total_bill"])
    value: Union[int, float] = Field(..., description="Numeric monetary value", examples=[1200])


class Step3ClassificationSuccessResponse(BaseModel):
    """Step 3: Classification by Context response schema."""
    amounts: List[ClassifiedAmountItem] = Field(..., description="List of classified amounts with types and values")
    confidence: float = Field(..., description="Classification confidence score", examples=[0.80])


class ProvenanceAmountItem(BaseModel):
    """Classified amount with original textual provenance for Step 4."""
    type: str = Field(..., description="Amount category", examples=["total_bill"])
    value: Union[int, float] = Field(..., description="Numeric monetary value", examples=[1200])
    source: str = Field(..., description="Exact source snippet provenance", examples=["text: 'Total: INR 1200'"])


class Step4FinalResponse(BaseModel):
    """Step 4: Final structured JSON output schema."""
    currency: str = Field("INR", description="Currency symbol or ISO code", examples=["INR"])
    amounts: List[ProvenanceAmountItem] = Field(..., description="Amounts labeled with context and source provenance")
    status: str = Field("ok", examples=["ok"])


# -------------------------------------------------------------
# Comprehensive Combined Pipeline Response (For Demo and Evaluators)
# -------------------------------------------------------------

class FullPipelineResponse(BaseModel):
    """Complete end-to-end response containing both the step breakdown and final output."""
    input_text: str = Field(..., description="Extracted or provided raw text")
    step1: Union[Step1ExtractionSuccessResponse, GuardrailResponse] = Field(..., description="Step 1 output")
    step2: Optional[Step2NormalizationSuccessResponse] = Field(None, description="Step 2 output (if not guarded)")
    step3: Optional[Step3ClassificationSuccessResponse] = Field(None, description="Step 3 output (if not guarded)")
    step4: Union[Step4FinalResponse, GuardrailResponse] = Field(..., description="Final Step 4 output adhering to spec")
    math_validation: Optional[Dict[str, Any]] = Field(None, description="Mathematical verification (Total == Paid + Due)")
