"""
BiofilmAI ML — Modality Encoders (legacy package path)
========================================================

Backwards-compatible re-exports. The canonical implementations live in
the flat modules:

    backend/ml/microscopy_encoder.py
    backend/ml/spectroscopy_encoder.py
    backend/ml/genomics_encoder.py
    backend/ml/clinical_encoder.py
"""

from ..microscopy_encoder import MicroscopyEncoder as VisionEncoder
from ..spectroscopy_encoder import SpectroscopyEncoder as SpectralEncoder
from ..genomics_encoder import GenomicsEncoder as GenomicEncoder
from ..clinical_encoder import ClinicalEncoder

__all__ = [
    "VisionEncoder",
    "SpectralEncoder",
    "GenomicEncoder",
    "ClinicalEncoder",
]
