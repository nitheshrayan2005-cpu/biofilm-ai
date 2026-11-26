"""
BiofilmAI ML — Model Loader & Checkpoint Interface
=====================================================

Unified interface for:
  - constructing a model from configuration
  - saving checkpoints (weights + optimizer state + metadata)
  - loading checkpoints
  - loading a standalone weights file
  - reporting model availability

Designed so the FastAPI demo pipeline works WITHOUT PyTorch: importing this
module only fails when `load_model()`/`build_model()` are actually called.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from .model_status import DEFAULT_WEIGHTS_PATH, REAL_MODEL_AVAILABLE, DEMO_MODE


def build_model(config=None):
    """
    Construct a MultimodalModel instance.

    Requires PyTorch. Raises ImportError with a clear message if torch
    is not installed.
    """
    try:
        from .multimodal_model import MultimodalModel
        from .model_config import default_config
    except ImportError as exc:
        raise ImportError(
            "PyTorch is required to build the real model. "
            "Install backend/ml/requirements-ml.txt. "
            "The API continues to run in DEMO MODE without it."
        ) from exc

    cfg = config or default_config()
    return MultimodalModel(cfg)


def load_weights(
    model,
    weights_path: str = DEFAULT_WEIGHTS_PATH,
    device: str = "cpu",
    strict: bool = True,
) -> bool:
    """
    Load a standalone weights file (.pt / .pth) into a model.

    Returns True on success, False if the file does not exist or fails
    to load. Never raises — the caller decides how to handle failure.
    """
    if not os.path.isfile(weights_path):
        return False
    try:
        import torch

        state_dict = torch.load(weights_path, map_location=device)
        # If the checkpoint bundles extra keys, unwrap a "model" sub-dict
        if isinstance(state_dict, dict) and "model_state" in state_dict:
            state_dict = state_dict["model_state"]
        model.load_state_dict(state_dict, strict=strict)
        return True
    except Exception:
        return False


def load_checkpoint(
    model,
    checkpoint_path: str,
    device: str = "cpu",
) -> Dict[str, Any]:
    """
    Load a full training checkpoint (weights + optimizer + metadata).

    Returns a dict with keys: "ok", "epoch", "metrics", "config"
    """
    if not os.path.isfile(checkpoint_path):
        return {"ok": False, "reason": f"checkpoint not found: {checkpoint_path}"}
    try:
        import torch

        ckpt = torch.load(checkpoint_path, map_location=device)
        if "model_state" in ckpt:
            model.load_state_dict(ckpt["model_state"])
        else:
            model.load_state_dict(ckpt)
        return {
            "ok": True,
            "epoch": ckpt.get("epoch"),
            "metrics": ckpt.get("metrics"),
            "config": ckpt.get("config"),
        }
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "reason": str(exc)}


def save_checkpoint(
    model,
    optimizer=None,
    epoch: int = 0,
    metrics: Optional[Dict[str, float]] = None,
    config: Any = None,
    path: str = "weights/biofilm_model.pt",
) -> str:
    """
    Save a full training checkpoint to disk.

    Creates the parent directory if needed. Returns the saved path.
    """
    import torch

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    payload: Dict[str, Any] = {
        "model_state": model.state_dict(),
        "epoch": epoch,
        "metrics": metrics or {},
        "config": config,
    }
    if optimizer is not None:
        payload["optimizer_state"] = optimizer.state_dict()
    torch.save(payload, path)
    return path


def model_availability() -> Dict[str, bool]:
    """Report whether the real model can be enabled right now."""
    return {
        "REAL_MODEL_AVAILABLE": REAL_MODEL_AVAILABLE,
        "DEMO_MODE": DEMO_MODE,
        "weights_exist": REAL_MODEL_AVAILABLE,
    }
