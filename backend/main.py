
"""
BiofilmAI Backend — FastAPI Application

Endpoints:
    POST  /api/auth/login
    GET   /api/auth/me
    POST  /api/analyze
    GET   /api/history
    GET   /api/analysis/{id}
    GET   /api/health
    POST  /api/research/genomic-predict
    POST  /api/research/biofilm-thickness-predict

IMPORTANT:
- /api/analyze remains in DEMO MODE.
- Biofilm thickness prediction is research-only.
- Thickness prediction is NOT a clinical diagnosis.
"""

from __future__ import annotations

import json
import logging
import math
import time
from pathlib import Path
from typing import Optional

import joblib
import pandas as pd

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from auth import authenticate, create_token, current_doctor
from config import settings
from ml_manager import model_manager
from models import (
    AnalysisResponse,
    AnalysisSummary,
    HealthResponse,
)
from storage import storage
from validation import (
    validate_file,
    validate_sample_info,
    validate_clinical_data,
    basic_pii_check,
)
from services import run_demo_inference


# ── Logging ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("biofilm-ai")


# ── FastAPI app ──────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ── CORS ─────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Error handling ───────────────────────────────────────────────────────

class APIError(HTTPException):
    """Custom API error with structured response."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        field: str = "general",
    ):
        super().__init__(
            status_code=status_code,
            detail=detail,
        )
        self.field = field


@app.exception_handler(APIError)
async def api_error_handler(request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "field": exc.field,
            "message": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def general_error_handler(request, exc: Exception):
    logger.error("Unhandled error: %s", exc)

    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": (
                "Internal server error. "
                "Analysis could not be completed."
            ),
            "status_code": 500,
        },
    )


# ── Health check ────────────────────────────────────────────────────────

@app.get(
    "/api/health",
    response_model=HealthResponse,
    tags=["System"],
)
async def health_check():
    """Return API health and current model mode."""

    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        demo_mode=model_manager.is_demo,
        description=settings.DESCRIPTION,
    )


# ── Authentication ───────────────────────────────────────────────────────

@app.post("/api/auth/login", tags=["Auth"])
async def login(body: dict):
    """Sign in with a doctor username and password."""

    doctor = authenticate(body.get("username", ""), body.get("password", ""))
    logger.info("Doctor signed in: %s", doctor["username"])
    return {"token": create_token(doctor), "doctor": doctor}


@app.get("/api/auth/me", tags=["Auth"])
async def me(doctor: dict = Depends(current_doctor)):
    """Return the signed-in doctor."""

    return doctor


# ── Main analysis endpoint ──────────────────────────────────────────────

@app.post(
    "/api/analyze",
    response_model=AnalysisResponse,
    tags=["Analysis"],
)
async def analyze(
    sampleInfo: str = Form(
        ...,
        description="JSON string of sample information",
    ),
    clinicalData: str = Form(
        ...,
        description="JSON string of clinical data",
    ),
    microscopy: Optional[UploadFile] = File(
        None,
        description="Microscopy image file",
    ),
    spectroscopy: Optional[UploadFile] = File(
        None,
        description="Spectroscopy data file",
    ),
    genomics: Optional[UploadFile] = File(
        None,
        description="Genomic data file",
    ),
    doctor: dict = Depends(current_doctor),
):
    """
    Run the existing multimodal demo analysis.

    All predictions from this endpoint remain DEMO MODE.
    No clinical diagnosis is generated.
    """

    start_time = time.time()

    # Parse JSON fields
    try:
        sample_info = json.loads(sampleInfo)
    except json.JSONDecodeError:
        raise APIError(
            400,
            "Invalid JSON in sampleInfo",
            "sampleInfo",
        )

    try:
        clinical_data = json.loads(clinicalData)
    except json.JSONDecodeError:
        raise APIError(
            400,
            "Invalid JSON in clinicalData",
            "clinicalData",
        )

    # Validate sample information
    try:
        validate_sample_info(sample_info)
    except Exception as exc:
        raise APIError(
            400,
            str(exc),
            "sampleInfo",
        )

    # Validate clinical data
    try:
        validate_clinical_data(clinical_data)
    except Exception as exc:
        raise APIError(
            400,
            str(exc),
            "clinicalData",
        )

    # Validate microscopy upload
    try:
        validate_file(
            microscopy,
            "microscopy",
            settings.MICROSCOPY_EXTENSIONS,
        )
    except Exception as exc:
        raise APIError(
            400,
            str(exc),
            "microscopy",
        )

    # Validate spectroscopy upload
    try:
        validate_file(
            spectroscopy,
            "spectroscopy",
            settings.SPECTROSCOPY_EXTENSIONS,
        )
    except Exception as exc:
        raise APIError(
            400,
            str(exc),
            "spectroscopy",
        )

    # Validate genomics upload
    try:
        validate_file(
            genomics,
            "genomics",
            settings.GENOMICS_EXTENSIONS,
        )
    except Exception as exc:
        raise APIError(
            400,
            str(exc),
            "genomics",
        )

    # PII check (warnings only)
    pii_warnings = basic_pii_check(sample_info)

    if pii_warnings:
        logger.warning("PII warnings: %s", pii_warnings)

    # Run original demo inference
    try:
        response = run_demo_inference(
            sample_info=sample_info,
            clinical_data=clinical_data,
            microscopy_file=microscopy,
            spectroscopy_file=spectroscopy,
            genomics_file=genomics,
        )

    except Exception:
        logger.exception("Demo inference failed")

        raise APIError(
            500,
            "AI analysis is temporarily unavailable. Please try again.",
            "analysis",
        )

    # Store result
    storage.save(response)

    elapsed = time.time() - start_time

    logger.info(
        "Analysis %s by %s completed in %.3fs "
        "(probability=%s, category=%s, modalities=%s)",
        response.analysis_id,
        doctor["username"],
        elapsed,
        response.prediction.biofilm_probability,
        response.prediction.risk_category,
        list(response.modalities.keys()),
    )

    return response


# ── Analysis history ────────────────────────────────────────────────────

@app.get(
    "/api/history",
    response_model=list[AnalysisSummary],
    tags=["History"],
)
async def get_history(doctor: dict = Depends(current_doctor)):
    """List all analyses, newest first."""

    return storage.list_all()


# ── Retrieve one analysis ───────────────────────────────────────────────

@app.get(
    "/api/analysis/{analysis_id}",
    response_model=AnalysisResponse,
    tags=["Analysis"],
)
async def get_analysis(analysis_id: str, doctor: dict = Depends(current_doctor)):
    """Retrieve one saved analysis."""

    analysis = storage.get(analysis_id)

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail=f"Analysis '{analysis_id}' not found",
        )

    return analysis


# ── Genomic research endpoint ───────────────────────────────────────────

@app.post(
    "/api/research/genomic-predict",
    tags=["Research"],
)
async def genomic_predict(body: dict, doctor: dict = Depends(current_doctor)):
    """
    Research-only genomic classification.

    Requires exactly 343 schema features.
    This does not produce a biofilm diagnosis.
    """

    from ml.inference.genomic_research_service import get_service

    service = get_service()

    if not service.is_loaded:
        raise HTTPException(
            status_code=503,
            detail=(
                "Genomic model artifact unavailable. "
                "The clinical-facing system remains in DEMO MODE."
            ),
        )

    features = body.get("features")
    isolate_id = body.get("isolate_id")

    try:
        result = service.predict(features)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        )

    result["isolate_id"] = (
        isolate_id if isolate_id is not None else None
    )

    logger.info(
        "[research] genomic-predict isolate=%s -> %s (P_path=%s)",
        isolate_id,
        result["predicted_class"],
        result["probability_pathogenic"],
    )

    return result


# ── Biofilm thickness research endpoint ─────────────────────────────────

@app.post(
    "/api/research/biofilm-thickness-predict",
    tags=["Research"],
)
async def predict_biofilm_thickness(body: dict, doctor: dict = Depends(current_doctor)):
    """
    Research-only experimental biofilm thickness prediction.

    Input JSON:
    {
        "time": 0.5,
        "flow_rate_ul_min": 5,
        "channel": "FLAT"
    }

    Target: AVEG

    This is not a clinical diagnostic endpoint.
    """

    required_fields = [
        "time",
        "flow_rate_ul_min",
        "channel",
    ]

    missing = [
        key for key in required_fields
        if key not in body
    ]

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing required fields: {missing}",
        )

    # Validate input values
    try:
        time_value = float(body["time"])
        flow_rate = float(body["flow_rate_ul_min"])
        channel = body["channel"]

        if not math.isfinite(time_value):
            raise ValueError("time must be finite.")

        if not 0 <= time_value <= 1:
            raise ValueError(
                "time must be between 0 and 1."
            )

        if not math.isfinite(flow_rate) or flow_rate <= 0:
            raise ValueError(
                "flow_rate_ul_min must be finite and positive."
            )

        if not isinstance(channel, str):
            raise ValueError("channel must be a string.")

        channel = channel.strip().upper()

        allowed_channels = {
            "FLAT",
            "RC1",
            "RC2",
            "RC3",
            "RT1",
            "RT2",
            "RT3",
        }

        if channel not in allowed_channels:
            raise ValueError(
                "Unsupported channel. Choose FLAT, RC1, RC2, "
                "RC3, RT1, RT2, or RT3."
            )

    except (TypeError, ValueError, OverflowError) as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    # Locate saved model
    model_path = (
        Path(__file__).resolve().parent
        / "models"
        / "biofilm_dt.joblib"
    )

    if not model_path.is_file():
        raise HTTPException(
            status_code=503,
            detail="Biofilm thickness model artifact is unavailable.",
        )

    # Load model and predict
    try:
        model = joblib.load(model_path)

        X = pd.DataFrame([{
            "time": time_value,
            "flow_rate_ul_min": flow_rate,
            "channel": channel,
        }])

        prediction = float(model.predict(X)[0])

        if not math.isfinite(prediction):
            raise RuntimeError(
                "Model returned a non-finite prediction."
            )

    except Exception:
        logger.exception(
            "Biofilm thickness prediction failed."
        )

        raise HTTPException(
            status_code=503,
            detail=(
                "Biofilm thickness prediction is "
                "temporarily unavailable."
            ),
        )

    return {
        "model": "Decision Tree",
        "target": "AVEG",
        "predicted_thickness": prediction,
        "input": {
            "time": time_value,
            "flow_rate_ul_min": flow_rate,
            "channel": channel,
        },
        "research_only": True,
        "notice": (
            "Experimental dataset prediction only. "
            "Not a clinical diagnosis. "
            "Target units have not been confirmed."
        ),
    }


# ── Startup event ───────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    logger.info(
        "BiofilmAI API v%s starting",
        settings.APP_VERSION,
    )

    logger.info("Demo mode: %s", settings.DEMO_MODE)
    logger.info("CORS origins: %s", settings.CORS_ORIGINS)
    logger.info(
        "Upload limit: %s MB",
        settings.MAX_UPLOAD_SIZE_MB,
    )
    logger.info(
        "Docs: http://%s:%s/docs",
        settings.HOST,
        settings.PORT,
    )

    logger.info("Initializing model manager...")
    model_manager.initialize()

    logger.info("Model mode: %s", model_manager.model_mode)
    logger.info(
        "Weights path: %s",
        settings.MODEL_WEIGHTS_PATH,
    )


# ── Main entry point ────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
