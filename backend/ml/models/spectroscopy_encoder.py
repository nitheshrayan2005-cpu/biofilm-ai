"""
BiofilmAI ML — Models: Spectroscopy Encoder
=============================================

1D Transformer encoder for spectral data (wavelength/intensity).

Canonical implementation lives in backend/ml/spectroscopy_encoder.py;
this module is the `models` package interface (re-export).
"""

from __future__ import annotations

from ..spectroscopy_encoder import SpectroscopyEncoder

__all__ = ["SpectroscopyEncoder"]
