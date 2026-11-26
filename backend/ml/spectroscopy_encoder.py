"""
BiofilmAI ML — Spectroscopy Encoder (flat module)
====================================================

1D Transformer encoder for spectral data (wavelength / intensity).

Input:  (B, max_seq_len, input_dim) — z-score normalized spectra
Output: (B, hidden_dim) fixed-dim embedding

Requires PyTorch. Imported lazily by the model manager; never imported
by the FastAPI demo pipeline.
"""

from __future__ import annotations

from typing import Optional

import torch
import torch.nn as nn

from .model_config import SpectroscopyEncoderConfig


class SpectroscopyEncoder(nn.Module):
    """
    1D Transformer over spectral tokens.

    Each spectral point (wavelength, intensity) is linearly projected to a
    hidden dimension and processed by stacked self-attention layers. The
    sequence is then globally pooled to a fixed-size embedding.
    """

    def __init__(self, config: Optional[SpectroscopyEncoderConfig] = None):
        super().__init__()
        self.config = config or SpectroscopyEncoderConfig()

        self.input_proj = nn.Linear(self.config.input_dim, self.config.hidden_dim)
        self.pos_embed = nn.Parameter(
            torch.randn(1, self.config.max_seq_len, self.config.hidden_dim) * 0.02
        )

        layer = nn.TransformerEncoderLayer(
            d_model=self.config.hidden_dim,
            nhead=self.config.num_heads,
            dim_feedforward=self.config.hidden_dim * 4,
            dropout=self.config.dropout,
            activation=self.config.activation,
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(layer, num_layers=self.config.num_layers)
        self.norm = nn.LayerNorm(self.config.hidden_dim)

    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            x: (B, seq_len, input_dim) spectral tensor
            mask: (B, seq_len) boolean padding mask (True = valid)
        Returns:
            (B, hidden_dim) embedding
        """
        B, N, _ = x.shape
        x = self.input_proj(x) + self.pos_embed[:, :N, :]

        if mask is not None:
            # TransformerEncoderLayer expects True = position to ignore
            pad_mask = ~mask
        else:
            pad_mask = None

        x = self.encoder(x, src_key_padding_mask=pad_mask)
        x = self.norm(x)

        if mask is not None:
            weight = mask.unsqueeze(-1).float()
            x = (x * weight).sum(dim=1) / weight.sum(dim=1).clamp(min=1.0)
        else:
            x = x.mean(dim=1)

        return x


# Backwards-compatible alias
SpectralEncoder = SpectroscopyEncoder
