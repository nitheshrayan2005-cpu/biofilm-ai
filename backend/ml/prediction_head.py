"""
BiofilmAI ML — Prediction Head (flat module)
===============================================

Maps the fused multimodal representation to a biofilm risk probability
and a risk category.

Input:  (B, input_dim) fused representation
Output: (B, 1) sigmoid probability in [0, 1]
        risk category string ("low" | "intermediate" | "high")

Requires PyTorch. Imported lazily by the model manager.
"""

from __future__ import annotations

from typing import Optional, Tuple

import torch
import torch.nn as nn

from .model_config import PredictionHeadConfig


class PredictionHead(nn.Module):
    """2-layer MLP with sigmoid output."""

    def __init__(self, config: Optional[PredictionHeadConfig] = None):
        super().__init__()
        self.config = config or PredictionHeadConfig()
        self.net = nn.Sequential(
            nn.Linear(self.config.input_dim, self.config.hidden_dim),
            nn.GELU(),
            nn.Dropout(self.config.dropout),
            nn.Linear(self.config.hidden_dim, self.config.num_classes),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """(B, input_dim) → (B, 1) probability"""
        return self.net(x)

    @staticmethod
    def classify_risk(probability: float) -> str:
        """Map a probability to a risk category string."""
        if probability < 0.4:
            return "low"
        if probability < 0.7:
            return "intermediate"
        return "high"

    def predict_with_category(
        self, x: torch.Tensor
    ) -> Tuple[torch.Tensor, list[str]]:
        probs = self.forward(x)
        categories = [self.classify_risk(p.item()) for p in probs]
        return probs, categories
