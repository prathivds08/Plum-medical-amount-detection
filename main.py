"""
Main FastAPI Application Entrypoint.
Exposes endpoints for individual pipeline steps (Step 1 to Step 4),
an end-to-end processing endpoint for both text and image inputs,
and an interactive Web Dashboard.
"""
import os
from typing import Optional, Union, Dict, Any
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from config import HOST, PORT, DEBUG
from models import (
    TextInputRequest,
    Step2NormalizeRequest,
    Step3ClassifyRequest,
    Step4FinalRequest,
    Step1ExtractionSuccessResponse,
    Step2NormalizationSuccessResponse,
    Step3ClassificationSuccessResponse,
    Step4FinalResponse,
    GuardrailResponse,
    FullPipelineResponse,
)
from services.pipeline import MedicalAmountPipeline

app = FastAPI(
    title="AI-Powered Amount Detection in Medical Documents",
    description=(
        "Backend service that extracts financial amounts from medical bills and receipts. "
        "Implements OCR -> Numeric Normalization -> Context Classification -> Final Provenance Output "
        "with strict adherence to assignment JSON schemas and guardrails."
    ),
    version="1.0.0",
)

# Enable CORS for web clients and demo integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static folder for interactive web app
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

SAMPLE_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_data")
if os.path.exists(SAMPLE_DATA_DIR):
    app.mount("/sample_data", StaticFiles(directory=SAMPLE_DATA_DIR), name="sample_data")


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serves the interactive web demo dashboard."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AI-Powered Amount Detection API is running. Visit /docs for Swagger documentation."}


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI-Powered Amount Detection in Medical Documents",
        "version": "1.0.0"
    }


# -------------------------------------------------------------
# Individual Pipeline Step Endpoints
# -------------------------------------------------------------

@app.post(
    "/api/v1/step1-extract",
    tags=["Pipeline Steps"],
    response_model=Union[Step1ExtractionSuccessResponse, GuardrailResponse],
    summary="Step 1: OCR / Text Extraction",
    description="Extracts raw numeric tokens, percentage tokens, and currency hint. Triggers guardrail if document is too noisy."
)
async def step1_extract(request: Request):
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        file = form.get("file")
        if file and hasattr(file, "read"):
            contents = await file.read()
            res = MedicalAmountPipeline.process_image(contents)
            return res["step1"]
        form_text = form.get("text")
        if form_text:
            s1 = MedicalAmountPipeline.run_step1(str(form_text))
            return s1["response"]
    else:
        try:
            body = await request.json()
            text = body.get("text", "")
            if text:
                s1 = MedicalAmountPipeline.run_step1(text)
                return s1["response"]
        except Exception:
            pass

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Either JSON body with 'text' or multipart 'file' must be provided."
    )


@app.post(
    "/api/v1/step2-normalize",
    tags=["Pipeline Steps"],
    response_model=Step2NormalizationSuccessResponse,
    summary="Step 2: Numeric Normalization & Digit Error Correction",
    description="Corrects OCR digit errors (e.g., 'l200' -> 1200) and maps to clean numbers while excluding percentage rates."
)
async def step2_normalize(payload: Step2NormalizeRequest):
    s2 = MedicalAmountPipeline.run_step2(payload.raw_tokens)
    return s2


@app.post(
    "/api/v1/step3-classify",
    tags=["Pipeline Steps"],
    response_model=Step3ClassificationSuccessResponse,
    summary="Step 3: Classification by Context",
    description="Uses surrounding context text to label amounts into 'total_bill', 'paid', 'due', etc."
)
async def step3_classify(payload: Step3ClassifyRequest):
    s3 = MedicalAmountPipeline.run_step3(payload.normalized_amounts, payload.text)
    return s3


@app.post(
    "/api/v1/step4-final",
    tags=["Pipeline Steps"],
    response_model=Step4FinalResponse,
    summary="Step 4: Final Output with Provenance",
    description="Returns labeled amounts with detected currency and exact source snippet provenance."
)
async def step4_final(payload: Step4FinalRequest):
    s4 = MedicalAmountPipeline.run_step4(payload.amounts, payload.currency or "INR", payload.text)
    return s4


# -------------------------------------------------------------
# Universal End-to-End Processing Endpoints
# -------------------------------------------------------------

@app.post(
    "/api/v1/process",
    tags=["End-to-End"],
    response_model=FullPipelineResponse,
    summary="Universal End-to-End Processor (Text JSON)",
    description="Processes raw bill/receipt text through all 4 pipeline stages, returning intermediate steps and final JSON."
)
async def process_text_bill(payload: TextInputRequest):
    return MedicalAmountPipeline.process_text(payload.text)


@app.post(
    "/api/v1/process-image",
    tags=["End-to-End"],
    response_model=FullPipelineResponse,
    summary="Universal End-to-End Processor (Image Upload)",
    description="Extracts and processes amounts directly from an uploaded medical bill image (PNG, JPG, scanned document)."
)
async def process_image_bill(file: UploadFile = File(...)):
    contents = await file.read()
    return MedicalAmountPipeline.process_image(contents)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=DEBUG)
