"""
BiofilmAI ML — Vision Encoder (Microscopy)
=============================================
Vision Transformer for microscopy image encoding.

Architecture:
  Input Image (224×224×3) → Patch Embedding → Transformer Encoder → Modality Embedding

The encoder produces a fixed-size representation suitable for cross-attention fusion.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from ..config import VisionEncoderConfig


class PatchEmbedding(nn.Module):
    """Split image into patches and embed them."""
    
    def __init__(self, config: VisionEncoderConfig):
        super().__init__()
        self.patch_size = config.patch_size
        self.num_patches = (config.image_size // config.patch_size) ** 2
        self.proj = nn.Conv2d(
            config.in_channels,
            config.embed_dim,
            kernel_size=config.patch_size,
            stride=config.patch_size,
        )
        self.cls_token = nn.Parameter(torch.randn(1, 1, config.embed_dim))
        self.pos_embed = nn.Parameter(torch.randn(1, self.num_patches + 1, config.embed_dim))
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B = x.shape[0]
        x = self.proj(x)  # (B, embed_dim, H/P, W/P)
        x = x.flatten(2).transpose(1, 2)  # (B, num_patches, embed_dim)
        cls_tokens = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)
        x = x + self.pos_embed
        return x


class TransformerBlock(nn.Module):
    """Standard Transformer block with self-attention and MLP."""
    
    def __init__(self, hidden_dim: int, num_heads: int, dropout: float, mlp_ratio: float = 4.0):
        super().__init__()
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.attn = nn.MultiheadAttention(hidden_dim, num_heads, dropout=dropout, batch_first=True)
        self.norm2 = nn.LayerNorm(hidden_dim)
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim, int(hidden_dim * mlp_ratio)),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(int(hidden_dim * mlp_ratio), hidden_dim),
            nn.Dropout(dropout),
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm1(x)
        attn_out, attn_weights = self.attn(h, h, h)
        x = x + attn_out
        x = x + self.mlp(self.norm2(x))
        return x, attn_weights


class VisionEncoder(nn.Module):
    """
    Vision Transformer encoder for microscopy images.
    
    Args:
        config: VisionEncoderConfig with image size, patch size, etc.
    
    Input:
        x: (B, C, H, W) microscopy image tensor
    
    Output:
        embedding: (B, hidden_dim) modality representation
        attention_weights: (B, num_heads, seq_len, seq_len) attention maps (optional)
    """
    
    def __init__(self, config: Optional[VisionEncoderConfig] = None):
        super().__init__()
        self.config = config or VisionEncoderConfig()
        self.patch_embed = PatchEmbedding(self.config)
        self.blocks = nn.ModuleList([
            TransformerBlock(
                self.config.embed_dim,
                self.config.num_heads,
                self.config.dropout,
                self.config.mlp_ratio,
            )
            for _ in range(self.config.num_layers)
        ])
        self.norm = nn.LayerNorm(self.config.embed_dim)
        self.projection = nn.Linear(self.config.embed_dim, self.config.hidden_dim)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Forward pass.
        
        Args:
            x: (B, C, H, W) image tensor
        
        Returns:
            embedding: (B, hidden_dim) modality representation
            attention_weights: (B, num_heads, seq_len, seq_len) or None
        """
        x = self.patch_embed(x)
        attn_weights = None
        for block in self.blocks:
            x, attn_w = block(x)
            attn_weights = attn_w
        
        x = self.norm(x)
        # Use CLS token as the representation
        cls_token = x[:, 0]
        embedding = self.projection(cls_token)
        
        return embedding, attn_weights
    
    def encode_image(self, image_bytes: bytes, device: str = "cpu") -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Encode raw image bytes into a modality embedding.
        
        This is the high-level interface used by the inference pipeline.
        
        Args:
            image_bytes: Raw image file bytes
            device: Target device
        
        Returns:
            embedding: (1, hidden_dim) modality representation
            attention_weights: Optional attention weights
        """
        from PIL import Image
        import io
        import torchvision.transforms as T
        
        # Load image
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Preprocess
        transform = T.Compose([
            T.Resize((self.config.image_size, self.config.image_size)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        x = transform(img).unsqueeze(0).to(device)
        
        # Encode
        with torch.no_grad():
            embedding, attn = self.forward(x)
        
        return embedding, attn