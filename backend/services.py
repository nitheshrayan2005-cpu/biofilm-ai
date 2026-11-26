"""
BiofilmAI Backend — Demo inference service.

This module generates clearly labeled DEMO predictions.  The real multimodal
Transformer model will replace this service without changing the API contract.

The demo engine:
1. Accepts any combination of modalities (microscopy, spectroscopy, genomics, clinical)
2. Generates a random but realistic biofilm probability (0.0 – 1.0)
3. Classifies the probability into a risk category
4. Returns a structured response that matches the frontend AnalysisResponse type
5. Includes a DEMO_MODE flag that the frontend must display

The prediction is NEVER a clinical diagnosis — it is a model-estimated probability
produced by a simulated multimodal Transformer.

The future real model will have the same interface:
- Input: sample metadata, file bytes per modality, clinical JSON
- Output: probability, risk category, modality contributions, interpretation
"""

from __future__ import annotations

import hashlib
import logging
import random
import time
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import UploadFile

from models import (
    AnalysisResponse,
    ModalityInfo,
    Prediction,
    Interpretation,
    MicroscopyAttention,
    CrossAttentionMap,
)

from ml_manager import model_manager


def generate_analysis_id() -> str:
    """Generate a unique analysis ID."""
    return f"BA-{uuid.uuid4().hex[:12].upper()}"


def classify_risk(probability: float) -> str:
    """Classify probability into risk category."""
    if probability < 0.4:
        return "low"
    elif probability < 0.7:
        return "intermediate"
    else:
        return "high"


def generate_demo_prediction(
    has_microscopy: bool,
    has_spectroscopy: bool,
    has_genomics: bool,
    has_clinical: bool,
) -> tuple[float, str]:
    """
    Generate a demo prediction based on which modalities are available.

    The algorithm is a simple heuristic that biases the probability toward
    higher values when more modalities are provided.
    """
    # Base probability varies by modality count
    num_modalities = sum([has_microscopy, has_spectroscopy, has_genomics, has_clinical])

    # Each modality contributes a different base weight
    base = 0.3
    if has_microscopy:
        base += 0.12
    if has_spectroscopy:
        base += 0.10
    if has_genomics:
        base += 0.08
    if has_clinical:
        base += 0.10

    # Add random noise to simulate model variability
    noise = random.gauss(0, 0.12)
    probability = max(0.05, min(0.95, base + noise))

    # Round to 3 decimal places
    probability = round(probability, 3)
    risk_category = classify_risk(probability)

    return probability, risk_category


def generate_demo_cross_attention() -> CrossAttentionMap:
    """Generate a plausible cross-attention matrix for demo purposes."""
    rows = ["microscopy", "spectroscopy", "genomics", "clinical"]
    cols = rows[:]

    # Biased toward diagonal (self-attention) and modality interactions
    base_matrix = [
        [0.38, 0.22, 0.18, 0.22],
        [0.24, 0.34, 0.20, 0.22],
        [0.20, 0.22, 0.32, 0.26],
        [0.22, 0.24, 0.28, 0.26],
    ]

    # Add slight randomness
    values = []
    for row in base_matrix:
        noisy_row = [max(0.05, min(0.95, v + random.uniform(-0.04, 0.04))) for v in row]
        values.append([round(v, 3) for v in noisy_row])

    return CrossAttentionMap(rows=rows, cols=cols, values=values)


def run_demo_inference(
    sample_info: dict,
    clinical_data: dict,
    microscopy_file: Optional[UploadFile],
    spectroscopy_file: Optional[UploadFile],
    genomics_file: Optional[UploadFile],
) -> AnalysisResponse:
    """
    Run inference and return a structured AnalysisResponse.

    Attempts real model inference first. Falls back to demo mode
    if the model is not available (no weights loaded).

    Parameters:
    -----------
    sample_info : dict
        Sample metadata (IDs, type, context, etc.)
    clinical_data : dict
        Structured clinical information
    microscopy_file : UploadFile or None
        Microscopy image file
    spectroscopy_file : UploadFile or None
        Spectroscopy data file
    genomics_file : UploadFile or None
        Genomic data file

    Returns:
    --------
    AnalysisResponse
        Structured response with prediction, modalities, and interpretation
    """
    now = datetime.now(timezone.utc).isoformat()

    has_micro = microscopy_file is not None
    has_spec = spectroscopy_file is not None
    has_genom = genomics_file is not None
    has_clinical = bool(clinical_data.get("infectionContext") or clinical_data.get("sampleSite"))

    # ── Attempt real model inference ─────────────────────────────────
    logger = logging.getLogger(__name__)
    if not model_manager.is_demo:
        try:
            microscopy_bytes = microscopy_file.file.read() if microscopy_file else None
        except Exception:
            microscopy_bytes = None
            if has_micro:
                logger.warning("Could not read microscopy file for real model inference")
        try:
            spectroscopy_bytes = spectroscopy_file.file.read() if spectroscopy_file else None
        except Exception:
            spectroscopy_bytes = None
        try:
            genomics_bytes = genomics_file.file.read() if genomics_file else None
        except Exception:
            genomics_bytes = None

        try:
            model_result = model_manager.run_inference(
                sample_info=sample_info,
                clinical_data=clinical_data,
                microscopy_bytes=microscopy_bytes,
                spectroscopy_bytes=spectroscopy_bytes,
                genomics_bytes=genomics_bytes,
            )

            if model_result.get("prediction") is not None:
                probability = model_result["prediction"]
                risk_category = model_result["risk_category"]
                contributions = model_result.get("contributions", {})

                # Build modalities from model contributions
                modalities = {}
                if has_micro:
                    modalities["microscopy"] = ModalityInfo(
                        modality="microscopy",
                        available=True,
                        status="available",
                        file_name=microscopy_file.filename if microscopy_file else None,
                        file_size=microscopy_file.size if microscopy_file else None,
                        contribution_score=round(contributions.get("microscopy", 0), 3),
                    )
                if has_spec:
                    modalities["spectroscopy"] = ModalityInfo(
                        modality="spectroscopy",
                        available=True,
                        status="available",
                        file_name=spectroscopy_file.filename if spectroscopy_file else None,
                        file_size=spectroscopy_file.size if spectroscopy_file else None,
                        contribution_score=round(contributions.get("spectroscopy", 0), 3),
                    )
                if has_genom:
                    modalities["genomics"] = ModalityInfo(
                        modality="genomics",
                        available=True,
                        status="available",
                        file_name=genomics_file.filename if genomics_file else None,
                        file_size=genomics_file.size if genomics_file else None,
                        contribution_score=round(contributions.get("genomics", 0), 3),
                    )
                if has_clinical:
                    modalities["clinical"] = ModalityInfo(
                        modality="clinical",
                        available=True,
                        status="available",
                        contribution_score=round(contributions.get("clinical", 0), 3),
                    )

                interpretation = Interpretation(
                    microscopy_attention=MicroscopyAttention(
                        original_available=has_micro,
                        overlay_available=has_micro,
                        heatmap_available=has_micro,
                    ) if has_micro else None,
                    cross_attention=generate_demo_cross_attention(),
                )

                analysis_id = generate_analysis_id()
                return AnalysisResponse(
                    analysis_id=analysis_id,
                    sample_id=sample_info.get("sampleId", ""),
                    sample_type=sample_info.get("sampleType", ""),
                    status="completed",
                    created_at=now,
                    completed_at=now,
                    prediction=Prediction(
                        biofilm_probability=probability,
                        risk_category=risk_category,
                    ),
                    modalities=modalities,
                    interpretation=interpretation,
                    demo_mode=False,
                    model_mode="model",
                    message=None,
                )
        except Exception as e:
            logger.error(f"Real model inference failed: {e}. Falling back to demo.")

    # ── Demo mode inference (fallback) ───────────────────────────────
    # Generate demo prediction
    probability, risk_category = generate_demo_prediction(
        has_micro, has_spec, has_genom, has_clinical
    )

    # Build modality information
    modalities = {}
    if has_micro:
        modalities["microscopy"] = ModalityInfo(
            modality="microscopy",
            available=True,
            status="available",
            file_name=microscopy_file.filename if microscopy_file else None,
            file_size=microscopy_file.size if microscopy_file else None,
            contribution_score=round(random.uniform(0.6, 0.95), 3),
        )
    if has_spec:
        modalities["spectroscopy"] = ModalityInfo(
            modality="spectroscopy",
            available=True,
            status="available",
            file_name=spectroscopy_file.filename if spectroscopy_file else None,
            file_size=spectroscopy_file.size if spectroscopy_file else None,
            contribution_score=round(random.uniform(0.5, 0.9), 3),
        )
    if has_genom:
        modalities["genomics"] = ModalityInfo(
            modality="genomics",
            available=True,
            status="available",
            file_name=genomics_file.filename if genomics_file else None,
            file_size=genomics_file.size if genomics_file else None,
            contribution_score=round(random.uniform(0.4, 0.85), 3),
        )
    if has_clinical:
        modalities["clinical"] = ModalityInfo(
            modality="clinical",
            available=True,
            status="available",
            contribution_score=round(random.uniform(0.55, 0.9), 3),
        )

    # Build interpretation
    interpretation = Interpretation(
        microscopy_attention=MicroscopyAttention(
            original_available=has_micro,
            overlay_available=has_micro,
            heatmap_available=has_micro,
        ) if has_micro else None,
        cross_attention=generate_demo_cross_attention(),
    )

    # Build response
    analysis_id = generate_analysis_id()
    response = AnalysisResponse(
        analysis_id=analysis_id,
        sample_id=sample_info.get("sampleId", ""),
        sample_type=sample_info.get("sampleType", ""),
        status="completed",
        created_at=now,
        completed_at=now,
        prediction=Prediction(
            biofilm_probability=probability,
            risk_category=risk_category,
        ),
        modalities=modalities,
        interpretation=interpretation,
        demo_mode=True,
        model_mode="demo",
        message=(
            "DEMO MODE — No clinical prediction is being generated. "
            "This probability is a simulated output from the demo inference engine "
            "and should not be interpreted as a clinical diagnosis."
        ),
    )

    response.sample_id = sample_info.get("sampleId", "")
    response.sample_type = sample_info.get("sampleType", "")

    return response