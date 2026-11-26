"""
BiofilmAI ML — Genomics Preprocessing
=======================================
Preprocessing pipeline for genomic sequences.

Steps:
1. Parse FASTA/CSV/TXT to sequence string
2. Convert nucleotides to indices
3. Pad or truncate to max_seq_len
4. Create attention mask

Output: (1, max_seq_len) indices + (1, max_seq_len) mask
"""

from __future__ import annotations

from typing import Optional, Tuple

import torch

from ..config import GenomicEncoderConfig


NUCLEOTIDE_MAP = {"A": 0, "C": 1, "G": 2, "T": 3, "U": 3, "a": 0, "c": 1, "g": 2, "t": 3, "u": 3}


def preprocess_genomics(
    data_bytes: bytes,
    max_seq_len: int = 2048,
    device: str = "cpu",
) -> Optional[Tuple[torch.Tensor, torch.Tensor]]:
    """
    Preprocess genomic data.
    
    Args:
        data_bytes: Raw CSV/TXT/FASTA file bytes
        max_seq_len: Maximum sequence length
        device: Target device
    
    Returns:
        Tuple of:
        - indices: (1, max_seq_len) tensor
        - mask: (1, max_seq_len) boolean tensor
        Or None if failed
    """
    try:
        text = data_bytes.decode("utf-8", errors="ignore")
        lines = text.strip().split("\n")
        
        # Check FASTA format
        if lines[0].startswith(">"):
            sequence = "".join(line.strip() for line in lines if not line.startswith(">"))
        else:
            sequence = "".join(line.strip() for line in lines if line.strip())
        
        # Convert to indices
        indices = []
        for char in sequence[:max_seq_len]:
            idx = NUCLEOTIDE_MAP.get(char, 0)
            indices.append(idx)
        
        if not indices:
            return None
        
        # Pad
        seq_len = len(indices)
        if seq_len < max_seq_len:
            indices = indices + [0] * (max_seq_len - seq_len)
        
        idx_tensor = torch.tensor([indices], dtype=torch.long, device=device)
        mask_tensor = torch.tensor(
            [[1] * seq_len + [0] * (max_seq_len - seq_len)],
            dtype=torch.bool,
            device=device,
        )
        
        return idx_tensor, mask_tensor
    except Exception:
        return None