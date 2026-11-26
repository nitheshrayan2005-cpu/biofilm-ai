"""
BiofilmAI Data — Schema Definitions
=====================================

Defines the column names, file extensions, and data conventions
that a labelled dataset MUST follow to be compatible with the
multimodal model.

No dataset is bundled. This is a specification that a future data
provider must adhere to.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Required columns in the master metadata CSV ────────────────────────

SAMPLE_ID_COL = "sample_id"
"""Primary key. Unique identifier for each biological sample.
Must be a string without spaces, usable as a filename stem."""

LABEL_COL = "biofilm_label"
"""Binary target. 1 = biofilm detected, 0 = no biofilm detected.
Must be 0 or 1 for all training/validation samples. None for
unlabelled inference-only samples."""

SPLIT_COL = "dataset_split"
"""Optional. One of: train, val, test. If absent the splitter
will stratify automatically."""

MICROSCOPY_PATH_COL = "microscopy_path"
"""Relative path under the dataset root to the microscopy image.
Accepted extensions: .png, .jpg, .jpeg, .tiff, .tif."""

SPECTROSCOPY_PATH_COL = "spectroscopy_path"
"""Relative path under the dataset root to the spectroscopy file.
Accepted extensions: .csv, .txt, .xlsx."""

GENOMICS_PATH_COL = "genomics_path"
"""Relative path under the dataset root to the genomics file.
Accepted extensions: .csv, .txt, .fasta, .fa, .fna."""

CLINICAL_PATH_COL = "clinical_path"
"""Relative path under the dataset root to a clinical JSON file.
Alternatively clinical fields can be flat columns in the CSV
(see CLINICAL_FEATURE_COLS below)."""

# ── Optional flat clinical columns (alternative to JSON files) ─────────

CLINICAL_FEATURE_COLS: List[str] = [
    "infection_context",
    "chronicity_days",
    "implant_present",
    "sample_site",
    "previous_treatment",
    "previous_culture",
    "wound_or_implant",
    "notes",
    "collection_date",
    "sample_type",
]
"""If these columns exist in the master CSV they will be used
instead of loading a separate clinical JSON file."""

# ── Accepted file extensions ──────────────────────────────────────────

MICROSCOPY_EXTENSIONS: List[str] = [".png", ".jpg", ".jpeg", ".tiff", ".tif"]
SPECTROSCOPY_EXTENSIONS: List[str] = [".csv", ".txt"]
GENOMICS_EXTENSIONS: List[str] = [".csv", ".txt", ".fasta", ".fa", ".fna"]
CLINICAL_EXTENSIONS: List[str] = [".json"]

# ── Expected image dimensions (after preprocessing) ───────────────────

IMAGE_SIZE: int = 224
IMAGE_CHANNELS: int = 3

# ── Spectroscopy sequence length ──────────────────────────────────────

SPECTROSCOPY_MAX_LEN: int = 1024
SPECTROSCOPY_FEATURES: int = 2  # wavelength + intensity

# ── Genomics sequence length ──────────────────────────────────────────

GENOMICS_MAX_LEN: int = 2048
NUCLEOTIDE_VOCAB: int = 4  # A, C, G, T

# ── Clinical feature vector size ──────────────────────────────────────

CLINICAL_FEATURE_DIM: int = 32


@dataclass
class DatasetSpec:
    """Complete specification of the expected dataset structure."""

    # Paths
    dataset_root: str = ""
    metadata_csv: str = "sample_metadata.csv"

    # Directories
    microscopy_dir: str = "microscopy"
    spectroscopy_dir: str = "spectroscopy"
    genomics_dir: str = "genomics"
    clinical_dir: str = "clinical"

    # Split proportions (must sum to 1.0)
    train_split: float = 0.7
    val_split: float = 0.15
    test_split: float = 0.15

    # Constraints
    min_samples: int = 10
    min_samples_per_class: int = 3
    max_missing_modalities_per_sample: int = 2
    max_duplicate_samples: float = 0.0

    # Random seed for reproducibility
    seed: int = 42

    def validate(self) -> List[str]:
        """Validate the specification itself."""
        errors = []
        total = self.train_split + self.val_split + self.test_split
        if abs(total - 1.0) > 1e-6:
            errors.append(f"Splits must sum to 1.0 (got {total})")
        if self.min_samples < 1:
            errors.append("min_samples must be >= 1")
        return errors