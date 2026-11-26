"""
BiofilmAI ML — Models: Clinical Encoder
=========================================

MLP encoder for structured clinical features (32-dim vector).

Canonical implementation lives in backend/ml/clinical_encoder.py;
this module is the `models` package interface (re-export).
"""

from __future__ import annotations

from ..clinical_encoder import ClinicalEncoder

__all__ = ["ClinicalEncoder"]
