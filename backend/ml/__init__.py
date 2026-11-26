"""
BiofilmAI ML Pipeline
=====================
Modular multimodal research pipeline for biofilm-associated infection prediction.

Architecture:
  Microscopy  → Vision Encoder      → \
  Spectroscopy → Spectral Encoder   →  → Cross-Attention Fusion Transformer → Biofilm Risk
  Genomics    → Genomic Encoder     → /
  Clinical    → Clinical Encoder    → /

Each modality is encoded independently, then fused via cross-attention.
The model supports missing modalities using modality masks.

Status: Architecture implemented. No trained weights yet. DEMO MODE active.
"""

__version__ = "0.1.0"