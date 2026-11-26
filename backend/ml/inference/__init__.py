"""
BiofilmAI ML — Inference
==========================
Inference pipelines.

Imports are lazy: importing this package does NOT require PyTorch.

Exports:
    MultimodalPredictor      — multimodal model bridge (lazy, torch-gated)
    GenomicResearchService   — validated genomic LR research endpoint (numpy-only)
    GenomicPredictor         — MLP genomic interface (torch-gated)
"""

__all__ = ["MultimodalPredictor", "GenomicResearchService", "GenomicPredictor"]

try:  # torch is only needed when the real multimodal model is enabled
    from .predictor import MultimodalPredictor
except ImportError:  # pragma: no cover
    MultimodalPredictor = None  # type: ignore

try:  # numpy-only — the validated genomic LR research service
    from .genomic_research_service import (
        GenomicResearchService,
        get_service,
        predict_genomic_research,
    )
    __all__ += ["get_service", "predict_genomic_research"]
except ImportError:  # pragma: no cover
    pass

try:  # torch-gated MLP genomic interface
    from .genomic_predictor import GenomicPredictor, predict_genomic, model_status
    __all__ += ["predict_genomic", "model_status"]
except ImportError:  # pragma: no cover
    pass
