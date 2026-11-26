"""
BiofilmAI ML — Models: Microscopy Encoder
===========================================

Vision encoder for microscopy images (224×224 RGB).

Canonical implementation lives in backend/ml/microscopy_encoder.py;
this module is the `models` package interface (re-export) so the
multimodal scaffold imports from one place.
"""

from __future__ import annotations

from ..microscopy_encoder import MicroscopyEncoder

__all__ = ["MicroscopyEncoder"]
