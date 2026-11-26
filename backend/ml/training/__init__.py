"""
BiofilmAI ML — Training
=========================
Training pipeline for the multimodal model.

Imports are lazy: importing this package does NOT require PyTorch.
The Trainer is only imported when training is actually invoked.
"""

__all__ = ["Trainer"]

try:  # lazy — torch is only needed when training actually runs
    from .trainer import Trainer
except ImportError:  # pragma: no cover
    Trainer = None  # type: ignore
