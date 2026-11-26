"""
BiofilmAI ML — Preprocessing
===============================

Per-modality preprocessing pipelines.

Torch-free modules (always importable):
    genomic_features — k-mer / GC / length features from genome sequences

Torch-dependent modules (lazy — only needed for real model training/inference):
    microscopy, spectroscopy, genomics, clinical
"""

# ── Torch-free ─────────────────────────────────────────────────────────────
from .genomic_features import (
    extract_genomic_features,
    kmer_composition,
    sequence_to_features,
    feature_columns,
    FEATURE_DIM,
)

__all__ = [
    "extract_genomic_features",
    "kmer_composition",
    "sequence_to_features",
    "feature_columns",
    "FEATURE_DIM",
]

# ── Torch-dependent (lazy) ─────────────────────────────────────────────────
try:  # requires torch + torchvision
    from .microscopy import preprocess_microscopy
    from .spectroscopy import preprocess_spectroscopy
    from .genomics import preprocess_genomics
    from .clinical import preprocess_clinical

    __all__ += [
        "preprocess_microscopy",
        "preprocess_spectroscopy",
        "preprocess_genomics",
        "preprocess_clinical",
    ]
except ImportError:  # pragma: no cover — torch not installed
    pass
