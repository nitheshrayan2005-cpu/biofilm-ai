"""
BiofilmAI Data — Dataset Schema (strict per-sample structure)
===============================================================

Defines the strict, sample-centric dataset layout that real data must
follow before training can begin.

    dataset/
    ├── manifest.csv                 # REQUIRED index of all samples
    ├── sample_<id>/
    │   ├── microscopy/
    │   │   └── image.png           # PNG / JPG / TIFF (readable RGB image)
    │   ├── spectroscopy/
    │   │   └── spectra.csv         # CSV/TXT: (wavelength, intensity) numeric pairs
    │   ├── genomics/
    │   │   └── sequence.fasta      # FASTA / CSV / TXT nucleotide sequence
    │   ├── clinical/
    │   │   └── clinical.json       # JSON matching CLINICAL_SCHEMA below
    │   └── label.txt               # "0" or "1" (biofilm absent / present)

The manifest.csv explicitly records every sample:

    sample_id, microscopy_path, spectroscopy_path, genomics_path, clinical_path, label

Paths are relative to the dataset root. Every column except the modality
paths is REQUIRED; modality paths may be empty when a modality is missing
— missing modalities are reported, never fabricated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ── Manifest columns ───────────────────────────────────────────────────────

SAMPLE_ID_COL = "sample_id"
MICROSCOPY_COL = "microscopy_path"
SPECTROSCOPY_COL = "spectroscopy_path"
GENOMICS_COL = "genomics_path"
CLINICAL_COL = "clinical_path"
LABEL_COL = "label"
SPLIT_COL = "dataset_split"  # optional; if absent, splitter stratifies

MANIFEST_COLUMNS: List[str] = [
    SAMPLE_ID_COL,
    MICROSCOPY_COL,
    SPECTROSCOPY_COL,
    GENOMICS_COL,
    CLINICAL_COL,
    LABEL_COL,
]

# Optional flat clinical columns (alternative to JSON files)
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

# ── Per-modality subdirectories within a sample folder ─────────────────────

SUBDIR_MICROSCOPY = "microscopy"
SUBDIR_SPECTROSCOPY = "spectroscopy"
SUBDIR_GENOMICS = "genomics"
SUBDIR_CLINICAL = "clinical"
LABEL_FILENAME = "label.txt"

MODALITY_SUBDIRS: Dict[str, str] = {
    "microscopy": SUBDIR_MICROSCOPY,
    "spectroscopy": SUBDIR_SPECTROSCOPY,
    "genomics": SUBDIR_GENOMICS,
    "clinical": SUBDIR_CLINICAL,
}

# ── File extensions ────────────────────────────────────────────────────────

MICROSCOPY_EXTENSIONS: List[str] = [".png", ".jpg", ".jpeg", ".tiff", ".tif"]
SPECTROSCOPY_EXTENSIONS: List[str] = [".csv", ".txt"]
GENOMICS_EXTENSIONS: List[str] = [".csv", ".txt", ".fasta", ".fa", ".fna"]
CLINICAL_EXTENSIONS: List[str] = [".json"]

# ── Preprocessing output shapes (match backend/ml/model_config.py) ─────────

IMAGE_SIZE: int = 224
IMAGE_CHANNELS: int = 3
SPECTROSCOPY_MAX_LEN: int = 1024
SPECTROSCOPY_FEATURES: int = 2
GENOMICS_MAX_LEN: int = 2048
NUCLEOTIDE_VOCAB: int = 4
CLINICAL_FEATURE_DIM: int = 32

# ── Clinical JSON schema ───────────────────────────────────────────────────

CLINICAL_SCHEMA: Dict[str, str] = {
    "infectionContext": "str",
    "chronicityDays": "number",
    "implantPresent": "bool",
    "sampleSite": "str",
    "previousTreatment": "str",
    "previousCulture": "str",
    "additionalNotes": "str",
    "sampleType": "str",
    "woundOrImplant": "str",
}
CLINICAL_REQUIRED_FIELDS: List[str] = ["infectionContext", "chronicityDays"]


@dataclass
class DatasetSpec:
    """
    Configuration for locating and validating a dataset.

    Supports two layouts:
      - "manifest"  : dataset_root/manifest.csv + per-sample folders
      - "flat"      : legacy CSV with path columns (kept for compatibility)
    """

    dataset_root: str = ""
    manifest_file: str = "manifest.csv"
    metadata_csv: str = "sample_metadata.csv"   # legacy flat layout
    layout: str = "manifest"                    # "manifest" | "flat"

    # Split proportions (must sum to 1.0)
    train_split: float = 0.7
    val_split: float = 0.15
    test_split: float = 0.15

    # Constraints
    min_samples: int = 10
    min_samples_per_class: int = 3

    # Random seed for reproducible splitting
    seed: int = 42

    def validate(self) -> List[str]:
        errors = []
        total = self.train_split + self.val_split + self.test_split
        if abs(total - 1.0) > 1e-6:
            errors.append(f"Splits must sum to 1.0 (got {total})")
        if self.layout not in ("manifest", "flat"):
            errors.append(f"Unknown layout '{self.layout}'")
        return errors
