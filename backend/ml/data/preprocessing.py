"""
BiofilmAI Data — Preprocessing Interface
===========================================

Unified preprocessing entry points for all four modalities.

Each function dispatches to the per-modality preprocessing pipelines in
`backend/ml/preprocessing/`. The interfaces accept a file path (or raw
bytes) and return tensors ready for the encoders.

All functions return `None` on failure so that missing / invalid
modalities are *reported* rather than silently fabricated.
"""

from __future__ import annotations

from typing import Optional, Tuple

import torch


def preprocess_microscopy(
    path_or_bytes,
    image_size: int = 224,
    device: str = "cpu",
) -> Optional[torch.Tensor]:
    """
    Load and preprocess a microscopy image.

    Returns (1, 3, 224, 224) normalized tensor, or None on failure.
    """
    try:
        from backend.ml.preprocessing.microscopy import preprocess_microscopy as _impl
        data = _read(path_or_bytes)
        return _impl(data, target_size=image_size, device=device)
    except Exception:
        return None


def preprocess_spectroscopy(
    path_or_bytes,
    max_seq_len: int = 1024,
    device: str = "cpu",
) -> Optional[torch.Tensor]:
    """
    Load and preprocess spectroscopy data.

    Returns (1, 1024, 2) normalized tensor, or None if no valid numeric
    wavelength/intensity pairs are found.
    """
    try:
        from backend.ml.preprocessing.spectroscopy import preprocess_spectroscopy as _impl
        data = _read(path_or_bytes)
        return _impl(data, max_seq_len=max_seq_len, device=device)
    except Exception:
        return None


def preprocess_genomics(
    path_or_bytes,
    max_seq_len: int = 2048,
    device: str = "cpu",
) -> Optional[Tuple[torch.Tensor, torch.Tensor]]:
    """
    Load and preprocess genomic sequence data.

    Returns (tokens (1, 2048), mask (1, 2048)), or None if the file
    contains no valid nucleotide sequence.
    """
    try:
        from backend.ml.preprocessing.genomics import preprocess_genomics as _impl
        data = _read(path_or_bytes)
        return _impl(data, max_seq_len=max_seq_len, device=device)
    except Exception:
        return None


def preprocess_clinical(
    clinical_data: dict,
    device: str = "cpu",
) -> Optional[torch.Tensor]:
    """
    Encode structured clinical data into a (1, 32) feature tensor.

    Returns None if the clinical dict is empty or invalid.
    """
    try:
        from backend.ml.preprocessing.clinical import preprocess_clinical as _impl
        return _impl(clinical_data, device=device)
    except Exception:
        return None


def preprocess_sample(sample: dict, device: str = "cpu") -> dict:
    """
    Preprocess every modality of a sample record.

    `sample` is a dict produced by the loader with keys:
        sample_id, microscopy_path, spectroscopy_path, genomics_path,
        clinical_path, label

    Returns a dict with tensors for each *available* modality plus a
    modality_mask recording availability. Missing modalities are simply
    absent — they are not fabricated.
    """
    item: dict = {
        "sample_id": sample["sample_id"],
        "modality_mask": {},
    }
    if "label" in sample and sample["label"] is not None:
        item["label"] = float(sample["label"])

    if sample.get("microscopy_path"):
        t = preprocess_microscopy(sample["microscopy_path"], device=device)
        if t is not None:
            item["microscopy"] = t.squeeze(0)
            item["modality_mask"]["microscopy"] = True

    if sample.get("spectroscopy_path"):
        t = preprocess_spectroscopy(sample["spectroscopy_path"], device=device)
        if t is not None:
            item["spectroscopy"] = t.squeeze(0)
            item["modality_mask"]["spectroscopy"] = True

    if sample.get("genomics_path"):
        result = preprocess_genomics(sample["genomics_path"], device=device)
        if result is not None:
            tokens, mask = result
            item["genomics"] = tokens.squeeze(0)
            item["genomics_mask"] = mask.squeeze(0)
            item["modality_mask"]["genomics"] = True

    if sample.get("clinical_path") or sample.get("clinical_data"):
        clinical = sample.get("clinical_data") or _load_clinical(sample.get("clinical_path"))
        if clinical:
            t = preprocess_clinical(clinical, device=device)
            if t is not None:
                item["clinical"] = t.squeeze(0)
                item["modality_mask"]["clinical"] = True

    return item


def _read(path_or_bytes) -> bytes:
    """Accept either a file path or raw bytes."""
    if isinstance(path_or_bytes, (bytes, bytearray)):
        return bytes(path_or_bytes)
    with open(path_or_bytes, "rb") as f:
        return f.read()


def _load_clinical(path: Optional[str]) -> Optional[dict]:
    if not path:
        return None
    try:
        import json
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return None
