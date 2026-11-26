"""
BiofilmAI ML — Genomic Classifier Network (PyTorch)
=====================================================

Simple feed-forward classifier over genome-derived features.

Feature vector (built by preprocessing/genomic_features.py):
    - k-mer composition (k=1..4)        340 features
    - GC content                         1 feature
    - normalized sequence length         1 feature
    - N / ambiguity ratio                1 feature
    -------------------------------------
    total                               343 features

No label-derived field is ever part of the input.
"""

from __future__ import annotations

from typing import Optional

import torch
import torch.nn as nn


class GenomicClassifierNet(nn.Module):
    """Small MLP for genomic pathogenic-vs-commensal classification."""

    def __init__(self, input_dim: int = 343, hidden_dim: int = 64, dropout: float = 0.2):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)
