"""
BiofilmAI ML — Multimodal Transformer (flat module)
=====================================================

The complete multimodal transformer: four encoders feeding a
cross-attention fusion block.

    Microscopy   → MicroscopyEncoder   → ─┐
    Spectroscopy → SpectroscopyEncoder → ─┤
    Genomics     → GenomicsEncoder     → ─┼→ CrossAttentionFusion → multimodal repr.
    Clinical     → ClinicalEncoder     → ─┘

This module combines the encoders and the fusion layer into a single
callable component. The prediction head is applied by
`multimodal_model.py` on top of the fused representation.

Requires PyTorch. Imported lazily by the model manager.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn

from .microscopy_encoder import MicroscopyEncoder
from .spectroscopy_encoder import SpectroscopyEncoder
from .genomics_encoder import GenomicsEncoder
from .clinical_encoder import ClinicalEncoder
from .cross_attention import CrossAttentionFusion
from .model_config import MultimodalConfig, default_config


class MultimodalTransformer(nn.Module):
    """
    Encoders + cross-attention fusion. Produces the unified
    multimodal representation for a sample.
    """

    def __init__(self, config: Optional[MultimodalConfig] = None):
        super().__init__()
        self.config = config or default_config()

        self.microscopy_encoder = MicroscopyEncoder(self.config.vision)
        self.spectroscopy_encoder = SpectroscopyEncoder(self.config.spectroscopy)
        self.genomics_encoder = GenomicsEncoder(self.config.genomics)
        self.clinical_encoder = ClinicalEncoder(self.config.clinical)
        self.fusion = CrossAttentionFusion(self.config.fusion)

    def forward(
        self,
        microscopy: Optional[torch.Tensor] = None,
        spectroscopy: Optional[torch.Tensor] = None,
        genomics: Optional[torch.Tensor] = None,
        genomics_mask: Optional[torch.Tensor] = None,
        clinical: Optional[torch.Tensor] = None,
        modality_mask: Optional[Dict[str, torch.Tensor]] = None,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor], Dict[str, float]]:
        """
        Returns:
            unified: (B, output_dim) fused representation
            attention_weights: optional cross-attention weights
            contributions: per-modality contribution scores
        """
        embeddings: Dict[str, torch.Tensor] = {}

        if microscopy is not None:
            embeddings["microscopy"] = self.microscopy_encoder(microscopy)
        if spectroscopy is not None:
            embeddings["spectroscopy"] = self.spectroscopy_encoder(spectroscopy)
        if genomics is not None:
            embeddings["genomics"] = self.genomics_encoder(genomics, genomics_mask)
        if clinical is not None:
            embeddings["clinical"] = self.clinical_encoder(clinical)

        # Expose per-modality embeddings for interpretation
        self._last_embeddings = {k: v.detach() for k, v in embeddings.items()}

        unified, attn, contribs = self.fusion(embeddings, modality_mask)
        return unified, attn, contribs
