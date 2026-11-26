"""
BiofilmAI ML — Multimodal Model (flat module)
================================================

End-to-end model: four encoders → cross-attention fusion → prediction head.

    Microscopy   ──► MicroscopyEncoder    ─┐
    Spectroscopy ──► SpectroscopyEncoder  ─┼─► CrossAttentionFusion ─► PredictionHead
    Genomics     ──► GenomicsEncoder      ─┤        │
    Clinical     ──► ClinicalEncoder      ─┘        ▼
                                              unified representation

forward() returns a dict with:
    - "prediction":       (B, 1) sigmoid probability
    - "risk_category":    list[str]
    - "modality_embeddings": dict of per-modality embeddings
    - "contributions":    dict[str, float]
    - "attention":        optional cross-attention weights

Requires PyTorch. Imported lazily by the model manager.
"""

from __future__ import annotations

from typing import Dict, Optional

import torch
import torch.nn as nn

from .multimodal_transformer import MultimodalTransformer
from .prediction_head import PredictionHead
from .model_config import MultimodalConfig, default_config


class MultimodalModel(nn.Module):
    """Complete multimodal biofilm-risk model."""

    def __init__(self, config: Optional[MultimodalConfig] = None):
        super().__init__()
        self.config = config or default_config()
        self.transformer = MultimodalTransformer(self.config)
        self.prediction_head = PredictionHead(self.config.prediction_head)

    def forward(
        self,
        microscopy: Optional[torch.Tensor] = None,
        spectroscopy: Optional[torch.Tensor] = None,
        genomics: Optional[torch.Tensor] = None,
        genomics_mask: Optional[torch.Tensor] = None,
        clinical: Optional[torch.Tensor] = None,
        modality_mask: Optional[Dict[str, torch.Tensor]] = None,
        **kwargs,
    ) -> Dict:
        """
        Args:
            microscopy, spectroscopy, genomics, genomics_mask, clinical:
                per-modality tensors (any subset allowed)
            modality_mask: dict of modality name → (B,) bool availability
            **kwargs: ignored extra batch keys (e.g. "labels", "sample_ids")
                      so the model is compatible with the DataLoader collate
                      and the Trainer's ``model(**batch)`` call.
        """
        unified, attn, contribs = self.transformer(
            microscopy=microscopy,
            spectroscopy=spectroscopy,
            genomics=genomics,
            genomics_mask=genomics_mask,
            clinical=clinical,
            modality_mask=modality_mask,
        )

        probs, categories = self.prediction_head.predict_with_category(unified)

        return {
            "prediction": probs,
            "risk_category": categories,
            "unified_representation": unified,
            "modality_embeddings": self.transformer._last_embeddings
            if hasattr(self.transformer, "_last_embeddings") else {},
            "contributions": contribs,
            "attention": attn,
        }

    # ── Convenience helpers ──────────────────────────────────────────────

    def predict(
        self,
        microscopy: Optional[torch.Tensor] = None,
        spectroscopy: Optional[torch.Tensor] = None,
        genomics: Optional[torch.Tensor] = None,
        genomics_mask: Optional[torch.Tensor] = None,
        clinical: Optional[torch.Tensor] = None,
        modality_mask: Optional[Dict[str, torch.Tensor]] = None,
    ) -> Dict:
        """Inference-time forward (no gradients)."""
        self.eval()
        with torch.no_grad():
            return self.forward(
                microscopy=microscopy,
                spectroscopy=spectroscopy,
                genomics=genomics,
                genomics_mask=genomics_mask,
                clinical=clinical,
                modality_mask=modality_mask,
            )
