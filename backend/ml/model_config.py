"""
BiofilmAI ML — Model Configuration
=====================================

Central configuration for the real multimodal model.

All model hyper-parameters are defined here so they can be tuned without
touching the model source code. Configuration can be overridden through
dataclass fields or environment variables.

NOTE: This module defines the *architecture* configuration. It does NOT
contain any trained weights or learned parameters.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


# ── Shared encoder settings ────────────────────────────────────────────────

@dataclass
class EncoderConfig:
    """Base configuration shared by all modality encoders."""
    hidden_dim: int = 256
    dropout: float = 0.1
    activation: str = "gelu"


# ── Microscopy / Vision ────────────────────────────────────────────────────

@dataclass
class VisionEncoderConfig(EncoderConfig):
    """
    Configuration for the microscopy encoder.

    `backbone` selects a pretrained vision backbone. The canonical
    implementation supports:
      - "vit_base_patch16_224"   (torchvision ViT-B/16, ImageNet weights)
      - "resnet50"               (torchvision ResNet-50, ImageNet weights)
      - "custom"                 (the in-repo Vision Transformer, no pretrained weights)
    """
    backbone: str = "custom"
    image_size: int = 224
    in_channels: int = 3
    patch_size: int = 16
    embed_dim: int = 256
    num_layers: int = 6
    num_heads: int = 8
    mlp_ratio: float = 4.0
    pretrained: bool = True        # only used when backbone != "custom"


# ── Spectroscopy ───────────────────────────────────────────────────────────

@dataclass
class SpectroscopyEncoderConfig(EncoderConfig):
    """Configuration for the spectral encoder."""
    input_dim: int = 2            # (wavelength, intensity)
    max_seq_len: int = 1024
    hidden_dim: int = 256
    num_layers: int = 4
    num_heads: int = 8


# ── Genomics ───────────────────────────────────────────────────────────────

@dataclass
class GenomicsEncoderConfig(EncoderConfig):
    """Configuration for the genomic encoder."""
    vocab_size: int = 4           # A, C, G, T
    embed_dim: int = 128
    hidden_dim: int = 256
    max_seq_len: int = 2048
    num_layers: int = 4
    num_heads: int = 8


# ── Clinical ───────────────────────────────────────────────────────────────

@dataclass
class ClinicalEncoderConfig(EncoderConfig):
    """
    Configuration for the clinical encoder.

    `categorical_columns` lists categorical variables (one-hot encoded);
    `numerical_columns` lists continuous variables (standardized).
    The resulting feature vector size must equal CLINICAL_FEATURE_DIM.
    """
    categorical_columns: list = field(default_factory=lambda: [
        "infection_context", "sample_site", "previous_treatment",
        "previous_culture", "sample_type", "implant_present",
    ])
    numerical_columns: list = field(default_factory=lambda: [
        "chronicity_days",
    ])
    input_dim: int = 32
    hidden_dim: int = 256
    num_layers: int = 3


# ── Cross-attention fusion ─────────────────────────────────────────────────

@dataclass
class CrossAttentionConfig:
    """Configuration for cross-attention fusion."""
    hidden_dim: int = 256
    num_heads: int = 8
    num_layers: int = 4
    dropout: float = 0.1
    num_modalities: int = 4
    output_dim: int = 128


# ── Prediction head ────────────────────────────────────────────────────────

@dataclass
class PredictionHeadConfig:
    """Configuration for the prediction head."""
    input_dim: int = 128
    hidden_dim: int = 128
    dropout: float = 0.1
    num_classes: int = 1          # binary biofilm probability


# ── Complete model configuration ───────────────────────────────────────────

@dataclass
class MultimodalConfig:
    """Top-level configuration for the full multimodal model."""
    model_name: str = "biofilm_multimodal_v1"
    vision: VisionEncoderConfig = field(default_factory=VisionEncoderConfig)
    spectroscopy: SpectroscopyEncoderConfig = field(default_factory=SpectroscopyEncoderConfig)
    genomics: GenomicsEncoderConfig = field(default_factory=GenomicsEncoderConfig)
    clinical: ClinicalEncoderConfig = field(default_factory=ClinicalEncoderConfig)
    fusion: CrossAttentionConfig = field(default_factory=CrossAttentionConfig)
    prediction_head: PredictionHeadConfig = field(default_factory=PredictionHeadConfig)
    device: str = "cpu"
    weights_path: Optional[str] = None


def default_config() -> MultimodalConfig:
    """Build the default model configuration."""
    return MultimodalConfig(
        weights_path=os.getenv("BIOFILM_WEIGHTS_PATH", "weights/biofilm_model.pt"),
        device=os.getenv("BIOFILM_DEVICE", "cpu"),
    )
