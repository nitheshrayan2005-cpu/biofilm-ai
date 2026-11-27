"""
BiofilmAI Backend — Analysis service.

For every analysis this module:
1. Measures each uploaded file (evidence.py): microscopy coverage and
   clustering, Raman peaks and matrix band, genome statistics and marker
   genes, and clinical risk factors
2. Uses the trained multimodal Transformer when weights are available
3. Otherwise reports a transparent, rule-based evidence score: the average of
   the measured indicators, with each modality's contribution
4. Returns a response matching the frontend AnalysisResponse type

Neither score is a clinical diagnosis.
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
from evidence import (
    analyze_clinical,
    analyze_genome,
    analyze_microscopy,
    analyze_spectrum,
    combine,
    key_findings,
)


def generate_analysis_id() -> str:
    """Generate a unique analysis ID."""
    return f"BA-{uuid.uuid4().hex[:12].upper()}"


def measure_evidence(
    microscopy_file: Optional[UploadFile],
    spectroscopy_file: Optional[UploadFile],
    genomics_file: Optional[UploadFile],
    clinical_data: dict,
) -> dict:
    """
    Measure each uploaded file (see evidence.py). A file that cannot be
    analysed gets {"error": ...} instead of failing the whole analysis.
    """
    logger = logging.getLogger(__name__)
    measured = {}
    for name, upload, analyse in (
        ("microscopy", microscopy_file, analyze_microscopy),
        ("spectroscopy", spectroscopy_file, analyze_spectrum),
        ("genomics", genomics_file, lambda b: analyze_genome(b.decode("utf-8", errors="replace"))),
    ):
        if upload is None:
            continue
        try:
            data = upload.file.read()
        finally:
            upload.file.seek(0)
        try:
            measured[name] = analyse(data)
        except Exception as exc:
            logger.warning("Could not analyse %s file: %s", name, exc)
            measured[name] = {"error": f"This {name} file could not be analysed: {exc}"}
    measured["clinical"] = analyze_clinical(clinical_data)
    return measured


def classify_risk(probability: float) -> str:
    """Classify probability into risk category."""
    if probability < 0.4:
        return "low"
    elif probability < 0.7:
        return "intermediate"
    else:
        return "high"


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
    measured = measure_evidence(microscopy_file, spectroscopy_file, genomics_file, clinical_data)

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
                    evidence=measured,
                    findings=key_findings(measured),
                    demo_mode=False,
                    model_mode="model",
                    message=None,
                )
        except Exception as e:
            logger.error(f"Real model inference failed: {e}. Falling back to demo.")

    # ── Evidence score (no trained multimodal model) ─────────────────
    # The score is the average of the indicators measured from the uploads,
    # so it is deterministic and every part of it can be explained.
    probability, contributions, findings = combine(measured)
    probability = probability if probability is not None else 0.0
    risk_category = classify_risk(probability)
    indicators = {c["modality"]: c["indicator"] for c in contributions}

    modalities = {}
    for name, upload, present in (
        ("microscopy", microscopy_file, has_micro),
        ("spectroscopy", spectroscopy_file, has_spec),
        ("genomics", genomics_file, has_genom),
    ):
        if present:
            modalities[name] = ModalityInfo(
                modality=name,
                available=True,
                status="error" if "error" in measured.get(name, {}) else "available",
                file_name=upload.filename,
                file_size=upload.size,
                contribution_score=indicators.get(name),
            )
    if has_clinical:
        modalities["clinical"] = ModalityInfo(
            modality="clinical",
            available=True,
            status="available",
            contribution_score=indicators.get("clinical"),
        )

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
        evidence=measured,
        findings=findings,
        score_breakdown=contributions,
        demo_mode=False,
        model_mode="evidence_score",
        message=(
            "Evidence score combining the indicators measured from the uploaded files. "
            "It is not a clinical diagnosis."
        ),
    )

    response.sample_id = sample_info.get("sampleId", "")
    response.sample_type = sample_info.get("sampleType", "")

    return response