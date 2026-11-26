"""
BiofilmAI ML — Models: Genomics Encoder
=========================================

Transformer encoder for genomic sequences (integer tokens + mask).

Canonical implementation lives in backend/ml/genomics_encoder.py;
this module is the `models` package interface (re-export).
"""

from __future__ import annotations

from ..genomics_encoder import GenomicsEncoder

__all__ = ["GenomicsEncoder"]
