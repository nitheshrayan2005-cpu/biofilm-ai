"""
BiofilmAI ML — Cross-Attention Fusion Transformer
====================================================
Fusion module that combines modality embeddings via cross-attention.

Architecture:
  [M1, M2, M3, M4] → Cross-Attention Transformer → Unified Representation → Prediction

The fusion module learns relationships between modalities and produces
a unified representation for downstream prediction.
"""

from __future__ import annotations

from typing import Optional, Dict, List, Tuple

import torch
import torch.nn as nn
import torch.nn.functional as F

from ..config import FusionConfig


class CrossAttentionBlock(nn.Module):
    """Single cross-attention block."""
    
    def __init__(self, hidden_dim: int, num_heads: int, dropout: float):
        super().__init__()
        self.norm1 = nn.LayerNorm(hidden_dim)
        self.self_attn = nn.MultiheadAttention(hidden_dim, num_heads, dropout=dropout, batch_first=True)
        self.norm2 = nn.LayerNorm(hidden_dim)
        self.cross_attn = nn.MultiheadAttention(hidden_dim, num_heads, dropout=dropout, batch_first=True)
        self.norm3 = nn.LayerNorm(hidden_dim)
        self.mlp = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim * 4, hidden_dim),
            nn.Dropout(dropout),
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: (B, num_modalities, hidden_dim)
        
        Returns:
            output: (B, num_modalities, hidden_dim)
            cross_attn_weights: (B, num_heads, num_modalities, num_modalities)
        """
        # Self-attention
        h = self.norm1(x)
        attn_out, _ = self.self_attn(h, h, h)
        x = x + attn_out
        
        # Cross-attention (each modality attends to all others)
        h = self.norm2(x)
        cross_out, cross_weights = self.cross_attn(h, h, h)
        x = x + cross_out
        
        # MLP
        x = x + self.mlp(self.norm3(x))
        
        return x, cross_weights


class CrossAttentionFusion(nn.Module):
    """
    Cross-Attention Fusion Transformer.
    
    Takes modality embeddings and fuses them via cross-attention.
    Supports missing modalities via modality masks.
    
    Args:
        config: FusionConfig
    
    Input:
        modality_embeddings: Dict[str, (B, hidden_dim)] modality embeddings
        modality_mask: Dict[str, (B,)] availability masks
    
    Output:
        unified: (B, output_dim) unified representation
        cross_attention_weights: (B, num_heads, num_modalities, num_modalities)
        modality_contributions: Dict[str, float] per-modality contribution scores
    """
    
    def __init__(self, config: Optional[FusionConfig] = None):
        super().__init__()
        self.config = config or FusionConfig()
        self.num_modalities = self.config.num_modalities
        self.modality_names = ["microscopy", "spectroscopy", "genomics", "clinical"]
        
        # Project each modality embedding to fusion dimension
        self.modality_proj = nn.ModuleDict({
            name: nn.Linear(self.config.hidden_dim, self.config.fusion_dim)
            for name in self.modality_names
        })
        
        # Learnable modality token embeddings
        self.modality_tokens = nn.Parameter(
            torch.randn(1, self.num_modalities, self.config.fusion_dim) * 0.02
        )
        
        # Cross-attention transformer blocks
        self.blocks = nn.ModuleList([
            CrossAttentionBlock(
                self.config.fusion_dim,
                self.config.num_heads,
                self.config.dropout,
            )
            for _ in range(self.config.num_layers)
        ])
        
        # Final projection
        self.norm = nn.LayerNorm(self.config.fusion_dim)
        self.output_proj = nn.Linear(self.config.fusion_dim, self.config.output_dim)
    
    def forward(
        self,
        modality_embeddings: Dict[str, torch.Tensor],
        modality_mask: Optional[Dict[str, torch.Tensor]] = None,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor], Dict[str, float]]:
        """
        Forward pass with modality fusion.
        
        Args:
            modality_embeddings: Dict mapping modality names to (B, hidden_dim) tensors
            modality_mask: Dict mapping modality names to (B,) boolean masks
        
        Returns:
            unified: (B, output_dim) unified representation
            cross_attn_weights: (B, num_heads, num_modalities, num_modalities)
            modality_contributions: Dict[str, float]
        """
        B = next(iter(modality_embeddings.values())).shape[0]
        device = next(iter(modality_embeddings.values())).device
        
        # Build modality sequence
        modality_list = []
        for name in self.modality_names:
            if name in modality_embeddings:
                emb = modality_embeddings[name]
                proj = self.modality_proj[name](emb)
                # Add learnable modality token
                proj = proj + self.modality_tokens[:, self.modality_names.index(name), :]
                modality_list.append(proj)
            else:
                # Missing modality: zero embedding
                modality_list.append(torch.zeros(B, self.config.fusion_dim, device=device))
        
        x = torch.stack(modality_list, dim=1)  # (B, num_modalities, fusion_dim)
        
        # Apply cross-attention
        cross_attn_weights = None
        for block in self.blocks:
            x, cross_attn_weights = block(x)
        
        x = self.norm(x)
        unified = self.output_proj(x.mean(dim=1))  # (B, output_dim)
        
        # Compute modality contributions
        contributions = self._compute_contributions(x, modality_mask)
        
        return unified, cross_attn_weights, contributions
    
    def _compute_contributions(
        self, x: torch.Tensor, modality_mask: Optional[Dict[str, torch.Tensor]] = None
    ) -> Dict[str, float]:
        """Compute per-modality contribution scores."""
        with torch.no_grad():
            # Use attention weights to estimate contributions
            contributions = {}
            for i, name in enumerate(self.modality_names):
                # Normalize the modality embedding
                emb = x[:, i, :]
                if modality_mask and name in modality_mask:
                    mask = modality_mask[name].float()
                    emb = emb * mask.unsqueeze(-1)
                score = emb.norm(dim=-1).mean().item()
                contributions[name] = score
            
            # Normalize to sum to 1
            total = sum(contributions.values()) + 1e-8
            contributions = {k: v / total for k, v in contributions.items()}
        
        return contributions