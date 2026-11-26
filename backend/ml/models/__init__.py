"""
BiofilmAI ML — Models (canonical multimodal package)
======================================================

Multimodal research architecture scaffolding:

    Microscopy   → Vision Encoder    → ┐
    Spectroscopy → Spectral Encoder  → ┤
    Genomics     → Genomic Encoder   → ┼→ Cross-Attention Fusion → Multimodal
    Clinical     → Clinical Encoder  → ┘      Representation      → Prediction Head

STATUS: ARCHITECTURE ONLY — NOT TRAINED.
The model returns model_mode="untrained_multimodal" and never fabricates
a clinical prediction. No paired four-modality dataset exists yet.

The genomic Logistic Regression experiment is a SEPARATE validated
baseline/branch (see inference/genomic_research_service.py); it is not
part of this multimodal model.
"""

from .config import MultimodalConfig, default_config
from .microscopy_encoder import MicroscopyEncoder
from .spectroscopy_encoder import SpectroscopyEncoder
from .genomics_encoder import GenomicsEncoder
from .clinical_encoder import ClinicalEncoder
from .cross_attention_fusion import CrossAttentionFusion, CrossAttentionFusionBlock
from .multimodal_model import MultimodalModel

__all__ = [
    "MultimodalConfig",
    "default_config",
    "MicroscopyEncoder",
    "SpectroscopyEncoder",
    "GenomicsEncoder",
    "ClinicalEncoder",
    "CrossAttentionFusion",
    "CrossAttentionFusionBlock",
    "MultimodalModel",
]
