"""
BiofilmAI ML — Model Status Flags
====================================

Single source of truth for whether the real model is available.

    REAL_MODEL_AVAILABLE = False   → no trained weights exist
    DEMO_MODE            = True    → API serves demo predictions

These flags are checked at runtime by the model manager. They are NOT
computed from fake data — they reflect the actual presence of a trained
checkpoint on disk.
"""

from __future__ import annotations

import os

# Path where trained weights would live (keep in sync with backend/config.py)
DEFAULT_WEIGHTS_PATH: str = os.getenv(
    "BIOFILM_WEIGHTS_PATH", "weights/biofilm_model.pt"
)

# Whether a trained checkpoint file physically exists on disk
REAL_MODEL_AVAILABLE: bool = os.path.isfile(DEFAULT_WEIGHTS_PATH)

# Whether demo mode is active. When the real model is available AND the
# operator explicitly disables demo mode, this becomes False.
DEMO_MODE: bool = os.getenv("BIOFILM_DEMO_MODE", "true").lower() == "true"


def model_status() -> dict:
    """Return the current model status as a structured dict."""
    weights_exist = os.path.isfile(DEFAULT_WEIGHTS_PATH)
    real_enabled = weights_exist and not DEMO_MODE
    return {
        "REAL_MODEL_AVAILABLE": weights_exist,
        "DEMO_MODE": not real_enabled,
        "real_inference_enabled": real_enabled,
        "weights_path": DEFAULT_WEIGHTS_PATH,
        "weights_exist": weights_exist,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(model_status(), indent=2))
