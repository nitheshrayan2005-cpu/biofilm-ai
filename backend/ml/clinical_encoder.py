"""
BiofilmAI ML — Clinical Encoder (flat module)
================================================

MLP encoder for structured clinical variables.

Handles both categorical and numerical variables:
  - categorical columns are one-hot encoded before the model (in preprocessing)
  - numerical columns are standardized before the model

Input:  (B, input_dim) float tensor of encoded clinical features
Output: (B, hidden_dim) fixed-dim embedding

Requires PyTorch. Imported lazily by the model manager.
"""

from __future__ import annotations

from typing import Optional

import torch
import torch.nn as nn

from .model_config import ClinicalEncoderConfig


class ClinicalEncoder(nn.Module):
    """
    Multi-layer perceptron over clinical feature vectors.
    """

    def __init__(self, config: Optional[ClinicalEncoderConfig] = None):
        super().__init__()
        self.config = config or ClinicalEncoderConfig()

        layers: list[nn.Module] = []
        in_dim = self.config.input_dim
        for _ in range(self.config.num_layers - 1):
            layers.extend([
                nn.Linear(in_dim, self.config.hidden_dim),
                nn.GELU(),
                nn.Dropout(self.config.dropout),
            ])
            in_dim = self.config.hidden_dim
        layers.append(nn.Linear(in_dim, self.config.hidden_dim))
        layers.append(nn.LayerNorm(self.config.hidden_dim))

        self.net = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """(B, input_dim) → (B, hidden_dim)"""
        return self.net(x)


def encode_clinical_features(clinical_data: dict, device: str = "cpu"):
    """
    Standalone helper: convert a clinical-data dict into a (1, input_dim)
    feature tensor using the preprocessing pipeline.
    """
    from .preprocessing.clinical import preprocess_clinical
    return preprocess_clinical(clinical_data, device=device)


# Backwards-compatible alias
ClinicalDataEncoder = ClinicalEncoder
