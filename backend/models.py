"""
BiofilmAI Backend — Pydantic models for request/response validation.

These models define the API contract between the frontend and backend.
The response format mirrors the existing frontend `AnalysisResponse` interface.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


# ── Request models ──────────────────────────────────────────────────────────

class SampleInfo(BaseModel):
    """Identifiers and high-level context for the sample."""
    sample_id: str = Field(..., min_length=1, max_length=64, alias="sampleId")
    study_id: str = Field(..., min_length=1, max_length=64, alias="studyId")
    sample_type: str = Field(..., min_length=1, max_length=64, alias="sampleType")
    collection_date: Optional[str] = Field(None, alias="collectionDate")
    infection_context: Optional[str] = Field(None, alias="infectionContext")
    wound_or_implant: Optional[str] = Field(None, alias="woundOrImplant")
    notes: Optional[str] = Field(None, max_length=2000)

    class Config:
        populate_by_name = True


class ClinicalData(BaseModel):
    """Structured clinical / sample metadata."""
    infection_context: Optional[str] = Field(None, alias="infectionContext")
    chronicity_days: int = Field(0, ge=0, le=3650, alias="chronicityDays")
    implant_present: bool = Field(False, alias="implantPresent")
    sample_site: Optional[str] = Field(None, alias="sampleSite")
    previous_treatment: Optional[str] = Field(None, alias="previousTreatment")
    previous_culture: Optional[str] = Field(None, alias="previousCulture")
    additional_notes: Optional[str] = Field(None, alias="additionalNotes", max_length=2000)

    class Config:
        populate_by_name = True


class AnalyzeRequest(BaseModel):
    """Multimodal analysis request — files uploaded separately via multipart."""
    sample_info: SampleInfo = Field(..., alias="sampleInfo")
    clinical_data: ClinicalData = Field(..., alias="clinicalData")

    class Config:
        populate_by_name = True


# ── Response models ─────────────────────────────────────────────────────────

class Prediction(BaseModel):
    """Model-estimated probability and risk category."""
    biofilm_probability: float = Field(..., alias="biofilmProbability", ge=0, le=1)
    risk_category: str = Field(..., alias="riskCategory", pattern="^(low|intermediate|high)$")

    class Config:
        populate_by_name = True


class ModalityInfo(BaseModel):
    """Modality availability and representation status."""
    modality: str
    available: bool
    status: str = "available"
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    contribution_score: Optional[float] = None


class CrossAttentionMap(BaseModel):
    """Cross-modal attention matrix (demo values)."""
    rows: list[str]
    cols: list[str]
    values: list[list[float]]


class MicroscopyAttention(BaseModel):
    original_available: bool = True
    overlay_available: bool = True
    heatmap_available: bool = True


class Interpretation(BaseModel):
    microscopy_attention: Optional[MicroscopyAttention] = Field(None, alias="microscopyAttention")
    cross_attention: Optional[CrossAttentionMap] = Field(None, alias="crossAttention")

    class Config:
        populate_by_name = True


class AnalysisResponse(BaseModel):
    """
    Full analysis result returned to the frontend.

    The demo mode flag is ALWAYS True when this is returned by the
    demo inference engine.  The frontend MUST display a DEMO MODE banner.
    """
    analysis_id: str = Field(..., alias="analysisId")
    sample_id: str = Field(..., alias="sampleId")
    sample_type: str = Field("", alias="sampleType")
    status: str = "completed"
    created_at: str = Field(..., alias="createdAt")
    completed_at: Optional[str] = Field(None, alias="completedAt")
    prediction: Optional[Prediction] = None
    modalities: dict[str, ModalityInfo] = {}
    interpretation: Optional[Interpretation] = None
    demo_mode: bool = Field(True, alias="demoMode")
    model_mode: str = Field("demo", alias="modelMode")
    message: Optional[str] = None

    class Config:
        populate_by_name = True


class AnalysisSummary(BaseModel):
    """Compact summary used in history listing."""
    analysis_id: str = Field(..., alias="analysisId")
    sample_id: str = Field(..., alias="sampleId")
    sample_type: str = Field(..., alias="sampleType")
    created_at: str = Field(..., alias="createdAt")
    modalities: list[str]
    prediction: Optional[Prediction] = None
    status: str = "completed"
    demo_mode: bool = True

    class Config:
        populate_by_name = True


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "ok"
    version: str
    demo_mode: bool
    description: str