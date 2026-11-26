"""
BiofilmAI ML — Spectroscopy Preprocessing
===========================================
Preprocessing pipeline for spectroscopy data.

Steps:
1. Parse CSV/TXT to numeric arrays
2. Normalize (z-score)
3. Pad or truncate to max_seq_len
4. Convert to tensor

Output: (1, max_seq_len, 2) tensor (wavelength, intensity)
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import torch

from ..config import SpectralEncoderConfig


def preprocess_spectroscopy(
    data_bytes: bytes,
    max_seq_len: int = 1024,
    device: str = "cpu",
) -> Optional[torch.Tensor]:
    """
    Preprocess spectroscopy data.
    
    Args:
        data_bytes: Raw CSV/TXT file bytes
        max_seq_len: Maximum sequence length
        device: Target device
    
    Returns:
        tensor: (1, max_seq_len, 2) or None if failed
    """
    try:
        text = data_bytes.decode("utf-8", errors="ignore")
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        points = []
        for line in lines:
            parts = line.replace(",", "\t").replace(";", "\t").split()
            if len(parts) >= 2:
                try:
                    points.append([float(parts[0]), float(parts[1])])
                except ValueError:
                    continue
        
        if not points:
            return None
        
        arr = np.array(points[:max_seq_len], dtype=np.float32)
        
        # Normalize (z-score)
        mean = arr.mean(axis=0)
        std = arr.std(axis=0) + 1e-8
        arr = (arr - mean) / std
        
        # Pad
        if len(arr) < max_seq_len:
            arr = np.pad(arr, ((0, max_seq_len - len(arr)), (0, 0)), mode="constant")
        
        tensor = torch.tensor(arr, dtype=torch.float32, device=device).unsqueeze(0)
        return tensor
    except Exception:
        return None