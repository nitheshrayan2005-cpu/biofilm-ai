"""
BiofilmAI ML — Model Configuration

Central configuration for all model components.
Each parameter can be overridden via environment variables.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EncoderConfig:
    """Configuration for a single modality encoder."""
    hidden_dim: int = 256
    num_layers: int = 4
    num_heads: int = 8
    dropout: float = 0.1
    activation: str = "gelu"
    max_seq_len: int = 512


@dataclass
class VisionEncoderConfig(EncoderConfig):
    """Configuration for the microscopy vision encoder."""
    image_size: int = 224
    patch_size: int = 16
    in_channels: int = 3
    embed_dim: int = 256
    num_layers: int = 6
    num_heads: int = 8
    dropout: float = 0.1
    mlp_ratio: float = 4.0


@dataclass
class SpectralEncoderConfig(EncoderConfig):
    """Configuration for the spectroscopy encoder."""
    input_dim: int = 1
    max_seq_len: int = 1024
    hidden_dim: int = 256
    num_layers: int = 4
    num_heads: int = 8
    dropout: float = 0.1


@dataclass
class GenomicEncoderConfig(EncoderConfig):
    """Configuration for the genomics encoder."""
    vocab_size: int = 4  # A, C, G, T
    embed_dim: int = 128
    hidden_dim: int = 256
    num_layers: int = 4
    num_heads: int = 8
    max_seq_len: int = 2048
    dropout: float = 0.1


@dataclass
class ClinicalEncoderConfig(EncoderConfig):
    """Configuration for the clinical data encoder."""
    input_dim: int = 32  # Number of clinical features
    hidden_dim: int = 256
    num_layers: int = 2
    num_heads: int = 4
    dropout: float = 0.1


@dataclass
class FusionConfig:
    """Configuration for the cross-attention fusion transformer."""
    hidden_dim: int = 256
    num_layers: int = 4
    num_heads: int = 8
    dropout: float = 0.1
    activation: str = "gelu"
    num_modalities: int = 4
    fusion_dim: int = 256
    output_dim: int = 128


@dataclass
class PredictionHeadConfig:
    """Configuration for the prediction head."""
    input_dim: int = 128
    hidden_dim: int = 128
    num_classes: int = 1  # Binary: biofilm present/absent
    dropout: float = 0.1


@dataclass
class ModelConfig:
    """Complete model configuration."""
    vision: VisionEncoderConfig = field(default_factory=VisionEncoderConfig)
    spectral: SpectralEncoderConfig = field(default_factory=SpectralEncoderConfig)
    genomic: GenomicEncoderConfig = field(default_factory=GenomicEncoderConfig)
    clinical: ClinicalEncoderConfig = field(default_factory=ClinicalEncoderConfig)
    fusion: FusionConfig = field(default_factory=FusionConfig)
    prediction_head: PredictionHeadConfig = field(default_factory=PredictionHeadConfig)
    
    # Global settings
    model_name: str = "biofilm_multimodal_v1"
    device: str = "cpu"
    weight_path: Optional[str] = None
    demo_mode: bool = True


@dataclass
class TrainingConfig:
    """Configuration for training."""
    epochs: int = 100
    batch_size: int = 32
    learning_rate: float = 1e-4
    weight_decay: float = 1e-5
    warmup_steps: int = 100
    max_grad_norm: float = 1.0
    early_stopping_patience: int = 10
    checkpoint_dir: str = "weights/"
    log_interval: int = 10
    val_split: float = 0.2
    test_split: float = 0.1
    random_seed: int = 42


@dataclass
class EvaluationConfig:
    """Configuration for evaluation."""
    metrics: list[str] = field(default_factory=lambda: [
        "accuracy", "precision", "recall", "f1", "roc_auc", "pr_auc"
    ])
    threshold: float = 0.5
    bootstrap_n: int = 1000
    confidence_level: float = 0.95


def get_model_config() -> ModelConfig:
    """Get the model configuration, overridden by environment variables."""
    config = ModelConfig()
    
    # Override from environment
    if os.getenv("BIOFILM_WEIGHTS_PATH"):
        config.weight_path = os.getenv("BIOFILM_WEIGHTS_PATH")
    if os.getenv("BIOFILM_DEMO_MODE", "true").lower() == "true":
        config.demo_mode = True
    else:
        config.demo_mode = False
    if os.getenv("BIOFILM_DEVICE"):
        config.device = os.getenv("BIOFILM_DEVICE")
    
    return config


def get_training_config() -> TrainingConfig:
    """Get the training configuration."""
    return TrainingConfig()


def get_evaluation_config() -> EvaluationConfig:
    """Get the evaluation configuration."""
    return EvaluationConfig()