"""
BiofilmAI ML — Microscopy Preprocessing
=========================================
Preprocessing pipeline for microscopy images.

Steps:
1. Load image from bytes
2. Resize to target size
3. Convert to RGB
4. Normalize with ImageNet statistics
5. Convert to tensor

Output: (1, 3, H, W) tensor
"""

from __future__ import annotations

import io
from typing import Optional

import torch
import torchvision.transforms as T

from PIL import Image


def preprocess_microscopy(
    image_bytes: bytes,
    target_size: int = 224,
    device: str = "cpu",
) -> Optional[torch.Tensor]:
    """
    Preprocess a microscopy image.
    
    Args:
        image_bytes: Raw image file bytes
        target_size: Target image size (square)
        device: Target device
    
    Returns:
        tensor: (1, 3, target_size, target_size) or None if failed
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        transform = T.Compose([
            T.Resize((target_size, target_size)),
            T.ToTensor(),
            T.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])
        tensor = transform(img).unsqueeze(0).to(device)
        return tensor
    except Exception:
        return None