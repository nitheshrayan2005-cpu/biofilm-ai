"""
BiofilmAI ML — Genomics Encoder (flat module)
================================================

Transformer encoder for genomic / sequence-derived numerical features.

The encoder accepts integer-encoded nucleotide sequences (A=0, C=1, G=2,
T=3) OR arbitrary numerical feature vectors. A padding mask allows
variable-length sequences to be batched.

Input:  (B, max_seq_len) long tensor + optional (B, max_seq_len) bool mask
Output: (B, hidden_dim) fixed-dim embedding

Requires PyTorch. Imported lazily by the model manager.
"""

from __future__ import annotations

from typing import Optional

import torch
import torch.nn as nn

from .model_config import GenomicsEncoderConfig


class GenomicsEncoder(nn.Module):
    """
    Token embedding + Transformer encoder for genomic sequences.
    """

    def __init__(self, config: Optional[GenomicsEncoderConfig] = None):
        super().__init__()
        self.config = config or GenomicsEncoderConfig()

        self.token_embed = nn.Embedding(self.config.vocab_size, self.config.embed_dim)
        # Positional embedding is added AFTER the projection to hidden_dim,
        # so it must match hidden_dim (was embed_dim — fixed shape bug).
        self.pos_embed = nn.Parameter(
            torch.randn(1, self.config.max_seq_len, self.config.hidden_dim) * 0.02
        )
        self.input_proj = nn.Linear(self.config.embed_dim, self.config.hidden_dim)

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
        tokens: torch.Tensor,
        mask: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        """
        Args:
            tokens: (B, seq_len) long tensor of nucleotide indices
            mask: (B, seq_len) bool tensor, True = valid token
        Returns:
            (B, hidden_dim) embedding
        """
        B, N = tokens.shape
        x = self.token_embed(tokens)                 # (B, N, embed_dim)
        x = self.input_proj(x) + self.pos_embed[:, :N, :]

        pad_mask = ~mask if mask is not None else None
        x = self.encoder(x, src_key_padding_mask=pad_mask)
        x = self.norm(x)

        if mask is not None:
            weight = mask.unsqueeze(-1).float()
            x = (x * weight).sum(dim=1) / weight.sum(dim=1).clamp(min=1.0)
        else:
            x = x.mean(dim=1)

        return x


# Backwards-compatible alias
GenomicEncoder = GenomicsEncoder
