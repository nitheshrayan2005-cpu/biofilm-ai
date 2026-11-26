"""
BiofilmAI ML — Models: Configuration
======================================

Configuration for the multimodal architecture. These are architecture
hyper-parameters only — no learned weights.

The four modality encoders project to a shared hidden_dim; the fusion
layer combines them into a unified representation; the prediction head
maps the unified representation to a single sigmoid output (reserved for
future training — the head is present but the model is NOT trained).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MultimodalConfig:
    """Top-level configuration for the multimodal scaffold."""

    model_name: str = "biofilm_multimodal_v1"

    # Shared encoder output dimension
    hidden_dim: int = 256

    # Vision encoder
    image_size: int = 224
    image_channels: int = 3
    vision_patch_size: int = 16
    vision_layers: int = 6
    vision_heads: int = 8

    # Spectral encoder
    spectroscopy_input_dim: int = 2        # (wavelength, intensity)
    spectroscopy_max_len: int = 1024
    spectroscopy_layers: int = 4
    spectroscopy_heads: int = 8

    # Genomics encoder
    genomics_vocab: int = 4                # A, C, G, T
    genomics_max_len: int = 2048
    genomics_embed_dim: int = 128
    genomics_layers: int = 4
    genomics_heads: int = 8

    # Clinical encoder
    clinical_input_dim: int = 32
    clinical_layers: int = 3

    # Fusion
    fusion_layers: int = 4
    fusion_heads: int = 8
    fusion_dropout: float = 0.1

    # Prediction head
    prediction_hidden_dim: int = 128

    # Explicit modality set (order is canonical)
    modalities: list = field(default_factory=lambda: [
        "microscopy", "spectroscopy", "genomics", "clinical",
    ])


def default_config() -> MultimodalConfig:
    return MultimodalConfig()
