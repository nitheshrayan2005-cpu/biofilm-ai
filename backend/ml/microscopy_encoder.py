"""
BiofilmAI ML — Microscopy Encoder (flat module)
=================================================

Vision encoder for microscopy images.

Canonical implementation with an optional pretrained backbone interface:

    backbone="resnet50"             → torchvision ResNet-50 (ImageNet weights)
    backbone="vit_base_patch16_224" → torchvision ViT-B/16 (ImageNet weights)
    backbone="custom"               → in-repo Vision Transformer (random init)

All backbones are projected to a fixed `hidden_dim` embedding (default 256).

NOTE: This module requires PyTorch. It is imported lazily by the model
manager only when the real model is enabled. The FastAPI demo pipeline
never imports this file.
"""

from __future__ import annotations

from typing import Optional, Tuple

import torch
import torch.nn as nn

from .model_config import VisionEncoderConfig


class CustomVisionTransformer(nn.Module):
    """
    Lightweight Vision Transformer used when no pretrained backbone is
    requested. Splits the image into patches, applies self-attention,
    and returns the CLS token embedding.
    """

    def __init__(self, config: VisionEncoderConfig):
        super().__init__()
        self.patch_size = config.patch_size
        self.num_patches = (config.image_size // config.patch_size) ** 2

        self.patch_embed = nn.Conv2d(
            config.in_channels,
            config.embed_dim,
            kernel_size=config.patch_size,
            stride=config.patch_size,
        )
        self.cls_token = nn.Parameter(torch.randn(1, 1, config.embed_dim))
        self.pos_embed = nn.Parameter(torch.randn(1, self.num_patches + 1, config.embed_dim))

        layer = nn.TransformerEncoderLayer(
            d_model=config.embed_dim,
            nhead=config.num_heads,
            dim_feedforward=int(config.embed_dim * config.mlp_ratio),
            dropout=config.dropout,
            activation=config.activation,
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=config.num_layers)
        self.norm = nn.LayerNorm(config.embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B = x.shape[0]
        x = self.patch_embed(x)                      # (B, E, H/P, W/P)
        x = x.flatten(2).transpose(1, 2)             # (B, N, E)
        cls = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls, x], dim=1) + self.pos_embed
        x = self.encoder(x)
        return self.norm(x[:, 0])                    # CLS token


class PretrainedVisionBackbone(nn.Module):
    """
    Wraps a torchvision pretrained backbone and projects its features
    to the fixed embedding dimension.
    """

    def __init__(self, config: VisionEncoderConfig):
        super().__init__()
        try:
            import torchvision.models as tv_models
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "torchvision is required for pretrained vision backbones. "
                "Install it or set backbone='custom'."
            ) from exc

        weights = "IMAGENET1K_V1" if config.pretrained else None

        if config.backbone == "resnet50":
            self.backbone = tv_models.resnet50(weights=weights)
            feat_dim = self.backbone.fc.in_features
            self.backbone.fc = nn.Identity()
        elif config.backbone == "vit_base_patch16_224":
            self.backbone = tv_models.vit_b_16(weights=weights)
            feat_dim = self.backbone.heads.head.in_features
            self.backbone.heads = nn.Identity()
        else:
            raise ValueError(f"Unknown backbone: {config.backbone}")

        self.projection = nn.Sequential(
            nn.Linear(feat_dim, config.embed_dim),
            nn.LayerNorm(config.embed_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        features = self.backbone(x)
        return self.projection(features)


class MicroscopyEncoder(nn.Module):
    """
    Full microscopy encoder.

    Input:  (B, 3, H, W) normalized RGB image
    Output: (B, hidden_dim) fixed-dim embedding
    """

    def __init__(self, config: Optional[VisionEncoderConfig] = None):
        super().__init__()
        self.config = config or VisionEncoderConfig()

        if self.config.backbone == "custom":
            self.encoder = CustomVisionTransformer(self.config)
        else:
            self.encoder = PretrainedVisionBackbone(self.config)

        # Final projection to hidden_dim if the backbone already outputs embed_dim
        self.norm = nn.LayerNorm(self.config.embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        out = self.encoder(x)
        return self.norm(out)


# Backwards-compatible alias used by the old nested import path
VisionEncoder = MicroscopyEncoder
