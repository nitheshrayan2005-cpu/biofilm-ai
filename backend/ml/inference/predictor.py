"""
BiofilmAI ML — Multimodal Predictor
=====================================
Inference pipeline that wraps the real multimodal model and produces
API-compatible responses.

This is the bridge between the PyTorch model and the FastAPI endpoints.
It reads raw file bytes, runs preprocessing + inference, and returns
results that the demo service can convert into the AnalysisResponse format.

This module imports PyTorch at the top level and is only imported lazily
by the model manager when the real model is enabled. The FastAPI demo
pipeline never imports it.
"""

from __future__ import annotations

import os
from typing import Optional, Dict, Any

import torch

from ..model_config import default_config
from ..model_loader import build_model, load_weights
from ..preprocessing import (
    preprocess_microscopy,
    preprocess_spectroscopy,
    preprocess_genomics,
    preprocess_clinical,
)


class MultimodalPredictor:
    """
    Production inference pipeline.

    Usage:
        predictor = MultimodalPredictor()
        predictor.load_model("weights/biofilm_model.pt")
        result = predictor.predict(
            microscopy_bytes=b"...",
            spectroscopy_bytes=b"...",
            genomics_bytes=b"...",
            clinical_data={...},
        )
    """

    def __init__(self, config=None, device: str = "cpu"):
        self.config = config or default_config()
        self.device = device
        self.model = None
        self.is_loaded = False

    def load_model(self, weight_path: str) -> bool:
        """Load trained weights into a freshly built model."""
        if not os.path.isfile(weight_path):
            print(f"[BiofilmAI] No weights found at {weight_path}")
            self.is_loaded = False
            return False

        try:
            self.config.weights_path = weight_path
            self.config.device = self.device
            self.model = build_model(self.config)
            ok = load_weights(self.model, weight_path, device=self.device)
            if ok:
                self.model.to(self.device)
                self.model.eval()
                self.is_loaded = True
                print(f"[BiofilmAI] Model loaded from {weight_path}")
            else:
                print(f"[BiofilmAI] Failed to load weights from {weight_path}")
                self.is_loaded = False
            return self.is_loaded
        except Exception as exc:  # pragma: no cover
            print(f"[BiofilmAI] Failed to load model: {exc}")
            self.is_loaded = False
            return False

    def predict(
        self,
        sample_info: dict,
        clinical_data: dict,
        microscopy_bytes: Optional[bytes] = None,
        spectroscopy_bytes: Optional[bytes] = None,
        genomics_bytes: Optional[bytes] = None,
    ) -> Dict[str, Any]:
        """Run real-model inference on one multimodal sample."""
        device = self.device
        modality_mask: Dict[str, torch.Tensor] = {}

        microscopy_t = (
            preprocess_microscopy(microscopy_bytes, device=device)
            if microscopy_bytes else None
        )
        if microscopy_t is not None:
            modality_mask["microscopy"] = torch.ones(1, dtype=torch.bool, device=device)

        spectroscopy_t = (
            preprocess_spectroscopy(spectroscopy_bytes, device=device)
            if spectroscopy_bytes else None
        )
        if spectroscopy_t is not None:
            modality_mask["spectroscopy"] = torch.ones(1, dtype=torch.bool, device=device)

        genomics_t = None
        genomics_mask = None
        if genomics_bytes:
            result = preprocess_genomics(genomics_bytes, device=device)
            if result is not None:
                genomics_t, genomics_mask = result
                modality_mask["genomics"] = torch.ones(1, dtype=torch.bool, device=device)

        clinical_t = preprocess_clinical(clinical_data, device=device)
        if clinical_t is not None:
            modality_mask["clinical"] = torch.ones(1, dtype=torch.bool, device=device)

        if self.model is not None and self.is_loaded:
            with torch.no_grad():
                output = self.model(
                    microscopy=microscopy_t,
                    spectroscopy=spectroscopy_t,
                    genomics=genomics_t,
                    genomics_mask=genomics_mask,
                    clinical=clinical_t,
                    modality_mask=modality_mask,
                )
            return {
                "prediction": output["prediction"].item(),
                "risk_category": output["risk_category"][0],
                "contributions": output["contributions"],
                "cross_attention": output["attention"],
                "model_mode": "model",
            }

        return {
            "prediction": None,
            "risk_category": None,
            "contributions": {},
            "cross_attention": None,
            "model_mode": "unavailable",
        }

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "loaded": self.is_loaded,
            "device": self.device,
            "weights_path": self.config.weights_path,
            "model_name": self.config.model_name,
        }
