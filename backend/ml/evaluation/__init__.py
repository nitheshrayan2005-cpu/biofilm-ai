"""
BiofilmAI ML — Evaluation
===========================
Evaluation pipeline for the multimodal model.

Imports are lazy: importing this package does NOT require PyTorch.
"""

__all__ = ["Evaluator"]

try:  # lazy — torch is only needed when evaluation actually runs
    from .evaluator import Evaluator
except ImportError:  # pragma: no cover
    Evaluator = None  # type: ignore
