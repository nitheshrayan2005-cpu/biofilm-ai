"""
BiofilmAI ML — Multimodal Model (legacy module path)
======================================================

This module exists for backwards compatibility with older import paths
(e.g. `from backend.ml.model import MultimodalModel`).

The canonical implementation now lives in the flat module
`backend/ml/multimodal_model.py`.
"""

from __future__ import annotations

from .multimodal_model import MultimodalModel
from .model_config import MultimodalConfig, default_config

__all__ = ["MultimodalModel", "MultimodalConfig", "default_config"]
