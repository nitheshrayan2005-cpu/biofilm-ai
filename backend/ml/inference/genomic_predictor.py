"""
BiofilmAI — Genomic Predictor (real model inference interface)
================================================================

Clean inference interface for the trained genomic classifier.

Input : a 343-feature vector (same schema as feature_schema.json)
Output: predicted class, per-class probabilities, model version,
        model_mode = "real_genomic_model"

DEMO MODE fallback: if trained weights are unavailable, predict() raises
a clear RuntimeError — it never returns a fabricated prediction. The
FastAPI demo pipeline is unaffected.

IMPORTANT: this model predicts pathogenic-vs-commensal status from
genomic features. It does NOT predict biofilm infection and makes no
clinical claim.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"
WEIGHTS_PATH = ARTIFACT_DIR / "genomic_classifier_best.pt"
FEATURE_SCHEMA_PATH = ARTIFACT_DIR / "feature_schema.json"
SCALER_PATH = ARTIFACT_DIR / "feature_scaler.json"

MODEL_VERSION = "genomic-v1.0"
MODEL_MODE = "real_genomic_model"


class GenomicPredictor:
    """Loads the trained weights once and exposes a predict() method."""

    def __init__(self, weights_path: str = str(WEIGHTS_PATH)):
        self.weights_path = weights_path
        self._model = None
        self._scaler_mean: Optional[np.ndarray] = None
        self._scaler_scale: Optional[np.ndarray] = None
        self.feature_schema: List[str] = []
        self.is_loaded = False

    def load(self) -> bool:
        """Load weights + scaler + feature schema. Returns True on success."""
        if not os.path.isfile(self.weights_path):
            return False
        try:
            import torch
            from backend.ml.models.arch import GenomicClassifierNet

            ckpt = torch.load(self.weights_path, map_location="cpu")
            self._model = GenomicClassifierNet(input_dim=343)
            self._model.load_state_dict(ckpt["model_state"])
            self._model.eval()

            scaler = json.load(open(SCALER_PATH))
            self._scaler_mean = np.array(scaler["mean"], dtype=np.float32)
            self._scaler_scale = np.array(scaler["scale"], dtype=np.float32)

            schema = json.load(open(FEATURE_SCHEMA_PATH))
            self.feature_schema = schema["features"]

            self.is_loaded = True
            return True
        except Exception:
            self.is_loaded = False
            return False

    def predict(self, features: np.ndarray) -> Dict:
        """
        Predict pathogenic vs commensal from a 343-feature vector.

        Args:
            features: array of shape (343,) or (n, 343) in the same order
                      as feature_schema.json
        Returns:
            dict with 'predicted_class', 'probabilities' {pathogenic, commensal},
            'model_version', 'model_mode'
        """
        if not self.is_loaded or self._model is None:
            raise RuntimeError(
                "NO TRAINED GENOMIC MODEL LOADED — cannot predict. "
                "The system remains in DEMO MODE until weights are available."
            )

        import torch

        x = np.asarray(features, dtype=np.float32)
        if x.ndim == 1:
            x = x.reshape(1, -1)
        if x.shape[1] != 343:
            raise ValueError(
                f"Expected 343 features, got {x.shape[1]}. "
                "Use the order in feature_schema.json."
            )

        # Apply the same standardization as training (fit on train only)
        x_scaled = (x - self._scaler_mean) / self._scaler_scale

        with torch.no_grad():
            prob = self._model(torch.tensor(x_scaled)).numpy().flatten()

        p_pathogenic = prob[0]
        p_commensal = 1.0 - p_pathogenic
        predicted = "pathogenic" if p_pathogenic >= 0.5 else "commensal"

        return {
            "predicted_class": predicted,
            "probabilities": {
                "pathogenic": round(float(p_pathogenic), 4),
                "commensal": round(float(p_commensal), 4),
            },
            "model_version": MODEL_VERSION,
            "model_mode": MODEL_MODE,
        }


def predict_genomic(features: np.ndarray) -> Dict:
    """Convenience function: load-once, then predict."""
    if not hasattr(predict_genomic, "_predictor"):
        predictor = GenomicPredictor()
        if not predictor.load():
            raise RuntimeError(
                "NO TRAINED GENOMIC MODEL AVAILABLE — cannot predict. "
                "The system remains in DEMO MODE until weights are available."
            )
        predict_genomic._predictor = predictor  # type: ignore
    return predict_genomic._predictor.predict(features)  # type: ignore


def model_status() -> Dict:
    """Report whether the real genomic model is available."""
    available = os.path.isfile(WEIGHTS_PATH)
    return {
        "real_genomic_model_available": available,
        "model_version": MODEL_VERSION if available else None,
        "model_mode": MODEL_MODE if available else "demo",
        "weights_path": str(WEIGHTS_PATH),
    }
