"""
BiofilmAI ML — Models: Cross-Attention Fusion
===============================================

Fuses the four modality embeddings using cross-attention.

Canonical implementation lives in backend/ml/cross_attention.py
(CrossAttentionFusion). This module is the `models` package interface
and adds `CrossAttentionFusionBlock` as an alias for the inner block.

The fusion layer NEVER assumes all modalities are present: it consumes a
modality mask and gives absent modalities zero contribution.
"""

from __future__ import annotations

from ..cross_attention import CrossAttentionFusion, CrossAttentionBlock

# Alias so `models` consumers can reference the inner block directly
CrossAttentionFusionBlock = CrossAttentionBlock

__all__ = ["CrossAttentionFusion", "CrossAttentionFusionBlock"]
