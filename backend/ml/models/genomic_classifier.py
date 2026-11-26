"""
BiofilmAI ML — Genomic Classifier (S. epidermidis)
====================================================

Binary classifier for the FIRST REAL EXPERIMENT:

    pathogenic (1) vs commensal (0)

Input features are derived ONLY from the genome sequence (k-mer
composition, GC content, length) — never from the Epidemiology label
or any field derived from it.

This module is import-safe WITHOUT PyTorch: it defines the interface and
reports GENOMIC_MODEL_AVAILABLE = False until real trained weights exist.
"""

from __future__ import annotations

import os

# Trained weights would live here (keep in sync with experiment config)
GENOMIC_WEIGHTS_PATH: str = os.getenv(
    "BIOFILM_GENOMIC_WEIGHTS", "weights/genomic_classifier.pt"
)

# Honest status — no trained weights exist in the project
GENOMIC_MODEL_AVAILABLE: bool = os.path.isfile(GENOMIC_WEIGHTS_PATH)


class GenomicClassifier:
    """
    Interface for the genomic pathogenic-vs-commensal classifier.

    NOT TRAINED. Instantiating or calling this class before real weights
    exist raises a clear error rather than returning a fake prediction.
    """

    def __init__(self, weights_path: str = GENOMIC_WEIGHTS_PATH):
        self.weights_path = weights_path
        self.is_loaded = False
        self._model = None

    def load(self) -> bool:
        """Load trained weights if they exist; otherwise return False."""
        if not GENOMIC_MODEL_AVAILABLE:
            return False
        try:
            import torch
            from .arch import GenomicClassifierNet

            self._model = GenomicClassifierNet()
            state = torch.load(self.weights_path, map_location="cpu")
            self._model.load_state_dict(state)
            self._model.eval()
            self.is_loaded = True
            return True
        except Exception:
            return False

    def predict(self, features):
        """
        Predict pathogenicity from genomic features.

        Raises RuntimeError when no trained model is loaded — it never
        returns a fabricated prediction.
        """
        if not self.is_loaded:
            raise RuntimeError(
                "NO TRAINED GENOMIC MODEL AVAILABLE — cannot predict. "
                "The system remains in DEMO MODE until weights exist."
            )
        import torch

        with torch.no_grad():
            prob = self._model(torch.tensor(features, dtype=torch.float32).unsqueeze(0))
        return {"pathogenic_probability": float(prob.item()), "model_mode": "model"}

    @staticmethod
    def status() -> dict:
        return {
            "GENOMIC_MODEL_AVAILABLE": GENOMIC_MODEL_AVAILABLE,
            "weights_path": GENOMIC_WEIGHTS_PATH,
            "target": "Epidemiology: pathogenic vs commensal",
            "input": "genome sequence features only",
        }
