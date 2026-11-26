"""
BiofilmAI ML — Genomic Feature Extraction (S. epidermidis)
============================================================

Builds numerical feature vectors from genome SEQUENCES ONLY.

Features (131 total):
    - k-mer composition for k = 1..4      128 features (normalized)
    - GC content                           1
    - normalized sequence length           1
    - N / ambiguity ratio                  1

IMPORTANT: No label-derived field (Epidemiology or any transformation of
it) is ever included in the feature vector. The label is used ONLY as the
prediction target.

This module requires no heavy dependencies (numpy only).
"""

from __future__ import annotations

from itertools import product
from typing import Dict, List, Optional

import numpy as np

KMERS = [1, 2, 3, 4]
ALPHABET = "ACGT"
FEATURE_DIM = sum(4 ** k for k in KMERS) + 3  # 340 + 3 = 343


def kmer_composition(sequence: str, k: int) -> np.ndarray:
    """Normalized k-mer frequency vector over ACGT."""
    counts = {}
    for i in range(len(sequence) - k + 1):
        kmer = sequence[i:i + k]
        counts[kmer] = counts.get(kmer, 0) + 1
    vec = np.zeros(4 ** k, dtype=np.float32)
    total = max(sum(counts.values()), 1)
    for kmer, count in counts.items():
        idx = 0
        for j, ch in enumerate(kmer):
            pos = ALPHABET.find(ch)
            if pos < 0:
                break
            idx += pos * (4 ** (k - 1 - j))
        else:
            vec[idx] = count / total
    return vec


def extract_genomic_features(sequence: str) -> np.ndarray:
    """
    Extract the 343-dim feature vector from a genomic sequence.

    (K-mer composition 340 + GC + length + N-ratio)
    """
    seq = sequence.upper()
    length = len(seq)
    if length == 0:
        raise ValueError("Empty sequence — cannot extract features")

    parts = [kmer_composition(seq, k) for k in KMERS]
    features = np.concatenate(parts)

    gc = (seq.count("G") + seq.count("C")) / length
    n_ratio = (seq.count("N") + sum(1 for c in seq if c not in "ACGT")) / length
    norm_length = min(length / 1_000_000.0, 10.0)  # normalize by ~1 Mb

    return np.concatenate([features, np.array([gc, norm_length, n_ratio], dtype=np.float32)])


def sequence_to_features(sequence: str) -> Optional[np.ndarray]:
    """Safe wrapper returning None on invalid/empty sequence."""
    try:
        return extract_genomic_features(sequence)
    except Exception:
        return None


def feature_columns() -> List[str]:
    """Human-readable names for each feature (for reporting only)."""
    cols = []
    for k in KMERS:
        for kmer in product(ALPHABET, repeat=k):
            cols.append("kmer_" + "".join(kmer))
    cols += ["gc_content", "norm_length", "n_ratio"]
    return cols
