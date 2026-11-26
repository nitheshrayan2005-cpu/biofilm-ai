"""
BiofilmAI — Genomic Research Inference Service
================================================

Backend-only research capability. Predicts **pathogenic vs commensal**
status from 343 genomic features using the trained Logistic Regression
model.

This is a RESEARCH endpoint. It is NOT connected to the clinical-facing
Results page, and its output must never be presented as "biofilm-associated
risk". See the research disclaimer in the response.

IMPORTANT:
  - validates the feature vector strictly (exact 343 names/order, numeric
    values only, rejects missing/extra/unknown features, never silently
    reorders)
  - returns model_mode = "real_genomic_model"
  - raises ValueError with a clear message on invalid input
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Dict, List, Union

import numpy as np

ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"
MODEL_JSON = ARTIFACT_DIR / "logistic_regression_model.json"

MODEL_VERSION = "genomic-lr-v1.0"
MODEL_MODE = "real_genomic_model"
EXPERIMENT_TARGET = "pathogenic_vs_commensal"

DISCLAIMER = (
    "Research model output: genomic classification of pathogenic vs commensal "
    "status. This is not a biofilm diagnosis, infection diagnosis, or clinical "
    "decision. Laboratory confirmation and professional judgment remain necessary."
)


def _sigmoid(z: float) -> float:
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    exp = math.exp(z)
    return exp / (1.0 + exp)


class GenomicResearchService:
    """Loads the LR model + scaler once and validates/predicts."""

    def __init__(self, model_json: str = str(MODEL_JSON)):
        self.model_json = model_json
        self._loaded = False
        self._coef: np.ndarray | None = None
        self._intercept: float = 0.0
        self._features: List[str] = []
        self._feature_set = set()
        self._mean: np.ndarray | None = None
        self._scale: np.ndarray | None = None

    # ── Loading ──────────────────────────────────────────────────────────

    def load(self) -> bool:
        """Load the model artifact. Returns False if unavailable."""
        try:
            with open(self.model_json) as f:
                art = json.load(f)
            self._features = list(art["features"])
            self._feature_set = set(self._features)
            self._coef = np.asarray(art["coefficients"], dtype=np.float64)
            self._intercept = float(art["intercept"])
            self._mean = np.asarray(art["scaler_mean"], dtype=np.float64)
            self._scale = np.asarray(art["scaler_scale"], dtype=np.float64)
            self._loaded = True
            return True
        except (OSError, KeyError, ValueError, json.JSONDecodeError):
            self._loaded = False
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def feature_count(self) -> int:
        return len(self._features) if self._features else 0

    # ── Validation ───────────────────────────────────────────────────────

    def validate_features(self, features: Dict[str, Union[int, float]]) -> np.ndarray:
        """
        Strictly validate a feature dict.

        Rules:
          - exactly the 343 expected feature names (schema order)
          - numeric values only (reject None, NaN, inf, strings, booleans)
          - reject missing / extra / unknown features
          - never silently reorder or guess unknown features
        Returns the feature vector in schema order.
        """
        if not self._loaded:
            raise RuntimeError(
                "Genomic model artifact unavailable. Cannot predict."
            )

        if not isinstance(features, dict):
            raise ValueError("'features' must be an object of {feature_name: value}")

        # 1) Exact key set must match the schema (no missing, no extra)
        keys = set(features.keys())
        if keys != self._feature_set:
            missing = sorted(self._feature_set - keys)
            extra = sorted(keys - self._feature_set)
            msg = "Feature vector must contain exactly the 343 schema features."
            if missing:
                msg += f" Missing {len(missing)}: {missing[:5]}{'...' if len(missing) > 5 else ''}"
            if extra:
                msg += f" Unknown/extra {len(extra)}: {extra[:5]}{'...' if len(extra) > 5 else ''}"
            raise ValueError(msg)

        # 2) Build vector in EXACT schema order
        vec = np.empty(self.feature_count, dtype=np.float64)
        for i, name in enumerate(self._features):
            v = features[name]
            # reject non-numeric (None, bool, str, complex)
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                raise ValueError(
                    f"Feature '{name}' must be numeric; got {type(v).__name__}."
                )
            vf = float(v)
            if not math.isfinite(vf):
                raise ValueError(f"Feature '{name}' must be finite (no NaN/inf).")
            vec[i] = vf
        return vec

    # ── Prediction ───────────────────────────────────────────────────────

    def predict(self, features: Dict[str, Union[int, float]]) -> Dict:
        """Validate + predict. Returns the research response dict."""
        if not self._loaded:
            raise RuntimeError(
                "Genomic model artifact unavailable. Cannot predict. "
                "The clinical-facing system remains in DEMO MODE."
            )
        vec = self.validate_features(features)

        # Standardize using the train-fit scaler
        scaled = (vec - self._mean) / self._scale
        z = float(np.dot(scaled, self._coef) + self._intercept)
        p_pathogenic = _sigmoid(z)
        p_commensal = 1.0 - p_pathogenic
        predicted = "pathogenic" if p_pathogenic >= 0.5 else "commensal"

        return {
            "predicted_class": predicted,
            "probability_pathogenic": round(p_pathogenic, 6),
            "probability_commensal": round(p_commensal, 6),
            "model_version": MODEL_VERSION,
            "model_mode": MODEL_MODE,
            "experiment_target": EXPERIMENT_TARGET,
            "research_disclaimer": DISCLAIMER,
        }


# Module-level singleton (loaded lazily on first use)
_service = None


def get_service() -> GenomicResearchService:
    global _service
    if _service is None:
        _service = GenomicResearchService()
        _service.load()
    return _service


def predict_genomic_research(features: Dict[str, Union[int, float]]) -> Dict:
    """Convenience: load-once, validate, predict."""
    return get_service().predict(features)
