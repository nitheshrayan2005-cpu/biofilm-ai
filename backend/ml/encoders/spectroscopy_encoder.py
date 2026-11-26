"""
BiofilmAI ML — Spectral Encoder (Spectroscopy)
================================================
Transformer encoder for spectroscopy data.

Architecture:
  Input Spectrum (N×2: wavelength, intensity) → Linear Embedding → Transformer → Modality Embedding

The encoder processes 1D spectral sequences.
"""

from __future__ import annotations

from typing import Optional, Tuple

import torch
import torch.nn as nn

from ..config import SpectralEncoderConfig


class SpectralEmbedding(nn.Module):
    """Embed 1D spectral data."""
    
    def __init__(self, config: SpectralEncoderConfig):
        super().__init__()
        self.proj = nn.Linear(config.input_dim, config.hidden_dim)
        self.pos_embed = nn.Parameter(torch.randn(1, config.max_seq_len, config.hidden_dim) * 0.02)
        self.norm = nn.LayerNorm(config.hidden_dim)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, N, _ = x.shape
        x = self.proj(x)
        x = x + self.pos_embed[:, :N, :]
        return self.norm(x)


class SpectralTransformerBlock(nn.Module):
    """Transformer block for spectral data."""
    
    def __init__(self, hidden_dim: int, num_heads: int, dropout: float):
        super().__init__()
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.attn = nn.MultiheadAttention(hidden_dim, num_heads, dropout=dropout, batch_first=True)
        self.norm2 = nn.LayerNorm(hidden_dim)
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 4, hidden_dim),
            nn.Dropout(dropout),
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.norm1(x)
        attn_out, attn_weights = self.attn(h, h, h)
        x = x + attn_out
        x = x + self.mlp(self.norm2(x))
        return x, attn_weights


class SpectralEncoder(nn.Module):
    """
    Transformer encoder for spectroscopy data.
    
    Args:
        config: SpectralEncoderConfig
    
    Input:
        x: (B, seq_len, input_dim) spectral sequence
        mask: (B, seq_len) padding mask (True = masked)
    
    Output:
        embedding: (B, hidden_dim) modality representation
        attention_weights: (B, num_heads, seq_len, seq_len) attention maps
    """
    
    def __init__(self, config: Optional[SpectralEncoderConfig] = None):
        super().__init__()
        self.config = config or SpectralEncoderConfig()
        self.embed = SpectralEmbedding(self.config)
        self.blocks = nn.ModuleList([
            SpectralTransformerBlock(
                self.config.hidden_dim,
                self.config.num_heads,
                self.config.dropout,
            )
            for _ in range(self.config.num_layers)
        ])
        self.norm = nn.LayerNorm(self.config.hidden_dim)
        self.projection = nn.Linear(self.config.hidden_dim, self.config.hidden_dim)
    
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Args:
            x: (B, seq_len, input_dim)
            mask: (B, seq_len) True = valid, False = padding
        
        Returns:
            embedding: (B, hidden_dim)
            attention_weights: Optional
        """
        x = self.embed(x)
        attn_weights = None
        for block in self.blocks:
            x, attn_w = block(x)
            attn_weights = attn_w
        
        x = self.norm(x)
        
        # Global average pooling over sequence dimension
        if mask is not None:
            mask_expanded = mask.unsqueeze(-1).float()
            x = (x * mask_expanded).sum(dim=1) / mask_expanded.sum(dim=1).clamp(min=1)
        else:
            x = x.mean(dim=1)
        
        embedding = self.projection(x)
        return embedding, attn_weights
    
    def encode_spectrum(self, data_bytes: bytes, device: str = "cpu") -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Encode raw spectroscopy file bytes into a modality embedding.
        
        Args:
            data_bytes: Raw CSV/TXT file bytes
            device: Target device
        
        Returns:
            embedding: (1, hidden_dim)
            attention_weights: Optional
        """
        import io
        import numpy as np
        
        text = data_bytes.decode("utf-8", errors="ignore")
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        # Parse CSV/TXT (expects wavelength, intensity)
        points = []
        for line in lines:
            parts = line.replace(",", "\t").replace(";", "\t").split()
            if len(parts) >= 2:
                try:
                    points.append([float(parts[0]), float(parts[1])])
                except ValueError:
                    continue
        
        if not points:
            # Return zero embedding for empty data
            return (torch.zeros(1, self.config.hidden_dim), None)
        
        # Pad or truncate to max_seq_len
        max_len = self.config.max_seq_len
        arr = np.array(points[:max_len], dtype=np.float32)
        
        # Normalize
        arr = (arr - arr.mean(axis=0)) / (arr.std(axis=0) + 1e-8)
        
        # Pad
        if len(arr) < max_len:
            arr = np.pad(arr, ((0, max_len - len(arr)), (0, 0)), mode="constant")
        
        x = torch.tensor(arr, dtype=torch.float32, device=device).unsqueeze(0)
        
        with torch.no_grad():
            embedding, attn = self.forward(x)
        
        return embedding, attn