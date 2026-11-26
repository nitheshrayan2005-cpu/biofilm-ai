"""
BiofilmAI ML — Cross-Attention Fusion (flat module)
======================================================

Fuses the four modality embeddings using cross-attention.

Each modality token attends to every other modality token through
stacked cross-attention blocks. Modality masks ensure missing modalities
do not contribute to attention.

Input:  dict of modality embeddings {name: (B, hidden_dim)}
        + optional modality mask {name: (B,) bool}
Output: (B, output_dim) unified multimodal representation
        + optional attention weights + per-modality contribution scores

Requires PyTorch. Imported lazily by the model manager.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import torch
import torch.nn as nn

from .model_config import CrossAttentionConfig

MODALITY_NAMES = ["microscopy", "spectroscopy", "genomics", "clinical"]

# Large finite negative value used to mask absent modalities in attention.
# float("-inf") is NOT used: an all-(-inf) row makes softmax return NaN, and
# that NaN then leaks into the attention keys and corrupts present rows.
MASK_VALUE = -1e9


class CrossAttentionBlock(nn.Module):
    """Self-attention + cross-attention + MLP block over modality tokens."""

    def __init__(self, dim: int, num_heads: int, dropout: float):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.self_attn = nn.MultiheadAttention(dim, num_heads, dropout=dropout, batch_first=True)
        self.norm2 = nn.LayerNorm(dim)
        self.cross_attn = nn.MultiheadAttention(dim, num_heads, dropout=dropout, batch_first=True)
        self.norm3 = nn.LayerNorm(dim)
        self.mlp = nn.Sequential(
            nn.Linear(dim, dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim * 4, dim),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor, attn_mask: Optional[torch.Tensor] = None):
        # Self-attention
        h = self.norm1(x)
        out, _ = self.self_attn(h, h, h, attn_mask=attn_mask)
        x = x + out

        # Cross-attention (each modality attends to all others)
        h = self.norm2(x)
        out, weights = self.cross_attn(h, h, h, attn_mask=attn_mask)
        x = x + out

        # MLP
        x = x + self.mlp(self.norm3(x))
        return x, weights


class CrossAttentionFusion(nn.Module):
    """
    Cross-attention fusion transformer over the four modality embeddings.

    Missing modalities receive zero embeddings and are excluded from
    attention via the modality mask.
    """

    def __init__(self, config: Optional[CrossAttentionConfig] = None):
        super().__init__()
        self.config = config or CrossAttentionConfig()
        self.num_modalities = self.config.num_modalities

        self.modality_proj = nn.ModuleDict({
            name: nn.Linear(self.config.hidden_dim, self.config.hidden_dim)
            for name in MODALITY_NAMES
        })
        self.modality_tokens = nn.Parameter(
            torch.randn(1, self.num_modalities, self.config.hidden_dim) * 0.02
        )

        self.blocks = nn.ModuleList([
            CrossAttentionBlock(
                self.config.hidden_dim,
                self.config.num_heads,
                self.config.dropout,
            )
            for _ in range(self.config.num_layers)
        ])

        self.norm = nn.LayerNorm(self.config.hidden_dim)
        self.output_proj = nn.Linear(self.config.hidden_dim, self.config.output_dim)

    def forward(
        self,
        modality_embeddings: Dict[str, torch.Tensor],
        modality_mask: Optional[Dict[str, torch.Tensor]] = None,
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor], Dict[str, float]]:
        B = next(iter(modality_embeddings.values())).shape[0]
        device = next(iter(modality_embeddings.values())).device

        tokens = []
        mask_list = []
        for i, name in enumerate(MODALITY_NAMES):
            if name in modality_embeddings:
                emb = self.modality_proj[name](modality_embeddings[name])
                emb = emb + self.modality_tokens[:, i, :]
                tokens.append(emb)
                mask_list.append(True)
            else:
                tokens.append(torch.zeros(B, self.config.hidden_dim, device=device))
                mask_list.append(False)

        x = torch.stack(tokens, dim=1)  # (B, 4, hidden_dim)

        # Build attention mask: a missing modality cannot attend or be attended.
        # Absent cells get MASK_VALUE (-1e9) — large but finite, so softmax
        # never produces NaN (see module docstring).
        attn_mask = None
        if modality_mask is not None:
            present = torch.tensor(
                [modality_mask.get(n, torch.tensor(False)).any().item() for n in MODALITY_NAMES],
                dtype=torch.bool,
                device=device,
            )
            attn_mask = torch.zeros(self.num_modalities, self.num_modalities, device=device)
            attn_mask.masked_fill_(~present.unsqueeze(0) | ~present.unsqueeze(1), MASK_VALUE)

        weights = None
        for block in self.blocks:
            x, weights = block(x, attn_mask=attn_mask)

        x = self.norm(x)

        # Pool only over present modalities.
        # Use the DIAGONAL of the attention mask: attn_mask[i, i] == 0.0 iff
        # modality i is present (absent cells hold MASK_VALUE).
        if attn_mask is not None:
            present = attn_mask.diag() == 0.0
            x_pooled = x[:, present, :].mean(dim=1)
        else:
            x_pooled = x.mean(dim=1)

        unified = self.output_proj(x_pooled)
        contributions = self._compute_contributions(x, attn_mask)

        return unified, weights, contributions

    def _compute_contributions(
        self, x: torch.Tensor, attn_mask: Optional[torch.Tensor]
    ) -> Dict[str, float]:
        """Per-modality contribution scores (normalized norms)."""
        with torch.no_grad():
            scores = {}
            for i, name in enumerate(MODALITY_NAMES):
                if attn_mask is not None and attn_mask[i, i] != 0.0:
                    scores[name] = 0.0
                else:
                    scores[name] = x[:, i, :].norm(dim=-1).mean().item()
            total = sum(scores.values()) + 1e-8
            return {k: round(v / total, 4) for k, v in scores.items()}
