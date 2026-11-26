"""
BiofilmAI ML — Cross-Attention Fusion (legacy package path)
=============================================================

Backwards-compatible re-export. The canonical implementation lives in
the flat module `backend/ml/cross_attention.py`.
"""

from ..cross_attention import CrossAttentionFusion, CrossAttentionBlock

__all__ = ["CrossAttentionFusion", "CrossAttentionBlock"]
