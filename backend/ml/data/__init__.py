"""
BiofilmAI ML — Data Module
============================

Dataset loading, validation, alignment, and splitting for multimodal
biofilm data.

This module does NOT bundle or download any dataset. The user must
prepare real data according to the schema specification (see README.md).

Strict per-sample pipeline:
    dataset_schema       — schema & manifest format
    modality_alignment   — sample↔modality alignment + missing detection
    dataset_checks       — the 10 validation rules
    validate_dataset     — CLI validation entry point
    preprocessing        — unified per-modality preprocessing interface
    dataset_loader       — genomic experiment loader (Excel + FASTA) + legacy loader
    fasta_parser         — FASTA parsing & sequence statistics

Validation, alignment, and the genomic experiment loader work WITHOUT
PyTorch. The torch-dependent loader/preprocessing are imported lazily.
"""

# ── Torch-free modules (always available) ──────────────────────────────────
from .dataset_schema import DatasetSpec, CLINICAL_SCHEMA, MANIFEST_COLUMNS
from .modality_alignment import (
    build_manifest,
    check_alignment,
    missing_modalities,
    split_samples,
)
from .dataset_checks import run_all_checks
from .fasta_parser import (
    FastaRecord,
    FastaStats,
    parse_fasta_file,
    header_id,
    normalize_id,
    sequence_is_valid,
)
from .dataset_loader import GenomicExperimentLoader, ExperimentManifest

__all__ = [
    "DatasetSpec",
    "CLINICAL_SCHEMA",
    "MANIFEST_COLUMNS",
    "build_manifest",
    "check_alignment",
    "missing_modalities",
    "split_samples",
    "run_all_checks",
    "FastaRecord",
    "FastaStats",
    "parse_fasta_file",
    "header_id",
    "normalize_id",
    "sequence_is_valid",
    "GenomicExperimentLoader",
    "ExperimentManifest",
]

# ── Torch-dependent modules (lazy) ─────────────────────────────────────────
try:  # torch is only required when actually loading/preprocessing data
    from .preprocessing import (
        preprocess_microscopy,
        preprocess_spectroscopy,
        preprocess_genomics,
        preprocess_clinical,
        preprocess_sample,
    )
    from .dataset import BiofilmDataset, DatasetLoader

    __all__ += [
        "preprocess_microscopy",
        "preprocess_spectroscopy",
        "preprocess_genomics",
        "preprocess_clinical",
        "preprocess_sample",
        "BiofilmDataset",
        "DatasetLoader",
    ]
except ImportError:  # pragma: no cover — torch not installed
    pass

# ── Legacy exports (compatibility; also torch-dependent, lazy) ─────────────
try:  # legacy modules require torch
    from .schema import DatasetSpec as LegacyDatasetSpec
    from .validator import DatasetValidator
    from .splitter import DatasetSplitter, apply_splits
    from .dataloader import get_dataloaders

    __all__ += [
        "LegacyDatasetSpec",
        "DatasetValidator",
        "DatasetSplitter",
        "apply_splits",
        "get_dataloaders",
    ]
except ImportError:  # pragma: no cover — torch not installed
    pass
