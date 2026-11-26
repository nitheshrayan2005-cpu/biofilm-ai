"""
BiofilmAI ML — Genomic Encoder
===============================
Transformer encoder for genomic sequences.

Architecture:
  Input Sequence (A/C/G/T) → Token Embedding → Transformer → Modality Embedding

Handles FASTA and CSV formats.
"""

from __future__ import annotations

from typing import Optional, Tuple

import torch
import torch.nn as nn

from ..config import GenomicEncoderConfig


# Nucleotide to index mapping
NUCLEOTIDE_MAP = {"A": 0, "C": 1, "G": 2, "T": 3, "U": 3, "a": 0, "c": 1, "g": 2, "t": 3, "u": 3}
PAD_TOKEN = 0


class GenomicEmbedding(nn.Module):
    """Embed nucleotide tokens."""
    
    def __init__(self, config: GenomicEncoderConfig):
        super().__init__()
        self.embedding = nn.Embedding(config.vocab_size, config.embed_dim)
        self.pos_embed = nn.Parameter(torch.randn(1, config.max_seq_len, config.embed_dim) * 0.02)
        self.norm = nn.LayerNorm(config.embed_dim)
        self.proj = nn.Linear(config.embed_dim, config.hidden_dim)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        B, N = x.shape
        x = self.embedding(x)
        x = x + self.pos_embed[:, :N, :]
        return self.proj(self.norm(x))


class GenomicTransformerBlock(nn.Module):
    """Transformer block for genomic data."""
    
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


class GenomicEncoder(nn.Module):
    """
    Transformer encoder for genomic sequences.
    
    Args:
        config: GenomicEncoderConfig
    
    Input:
        x: (B, seq_len) integer-encoded nucleotide sequence
        mask: (B, seq_len) padding mask
    
    Output:
        embedding: (B, hidden_dim) modality representation
        attention_weights: Optional attention maps
    """
    
    def __init__(self, config: Optional[GenomicEncoderConfig] = None):
        super().__init__()
        self.config = config or GenomicEncoderConfig()
        self.embed = GenomicEmbedding(self.config)
        self.blocks = nn.ModuleList([
            GenomicTransformerBlock(
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
            x: (B, seq_len) integer-encoded sequence
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
        
        # Global average pooling
        if mask is not None:
            mask_expanded = mask.unsqueeze(-1).float()
            x = (x * mask_expanded).sum(dim=1) / mask_expanded.sum(dim=1).clamp(min=1)
        else:
            x = x.mean(dim=1)
        
        embedding = self.projection(x)
        return embedding, attn_weights
    
    def encode_sequence(self, data_bytes: bytes, device: str = "cpu") -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        """
        Encode raw genomics file bytes into a modality embedding.
        
        Args:
            data_bytes: Raw CSV/TXT/FASTA file bytes
            device: Target device
        
        Returns:
            embedding: (1, hidden_dim)
            attention_weights: Optional
        """
        text = data_bytes.decode("utf-8", errors="ignore")
        lines = text.strip().split("\n")
        
        # Check if FASTA format
        if lines[0].startswith(">"):
            # FASTA: skip header lines, join sequence lines
            sequence = "".join(line.strip() for line in lines if not line.startswith(">"))
        else:
            # CSV/TXT: join all non-empty characters
            sequence = "".join(line.strip() for line in lines if line.strip())
        
        # Convert to indices
        indices = []
        for char in sequence[:self.config.max_seq_len]:
            idx = NUCLEOTIDE_MAP.get(char, 0)
            indices.append(idx)
        
        if not indices:
            return (torch.zeros(1, self.config.hidden_dim), None)
        
        # Pad
        if len(indices) < self.config.max_seq_len:
            indices = indices + [PAD_TOKEN] * (self.config.max_seq_len - len(indices))
        
        x = torch.tensor([indices], dtype=torch.long, device=device)
        mask = torch.tensor([[1] * len(sequence[:self.config.max_seq_len]) + [0] * (self.config.max_seq_len - len(sequence[:self.config.max_seq_len]))], dtype=torch.bool, device=device)
        
        with torch.no_grad():
            embedding, attn = self.forward(x, mask)
        
        return embedding, attn