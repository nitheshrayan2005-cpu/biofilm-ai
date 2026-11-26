"""
BiofilmAI Data — PyTorch Dataset
==================================

A PyTorch Dataset that loads multimodal samples from a structured dataset
directory.  It is designed to be compatible with the existing
MultimodalModel.forward() signature.

No dataset is loaded by default.  The Dataset will report its own
availability and clearly state when no real data is present.
"""

from __future__ import annotations

import json
import os
import warnings
from typing import Dict, List, Optional, Tuple

import torch
from torch.utils.data import Dataset

from ..config import ClinicalEncoderConfig

from .schema import (
    SAMPLE_ID_COL,
    LABEL_COL,
    SPLIT_COL,
    MICROSCOPY_PATH_COL,
    SPECTROSCOPY_PATH_COL,
    GENOMICS_PATH_COL,
    CLINICAL_PATH_COL,
    CLINICAL_FEATURE_COLS,
    MICROSCOPY_EXTENSIONS,
    SPECTROSCOPY_EXTENSIONS,
    GENOMICS_EXTENSIONS,
    IMAGE_SIZE,
    SPECTROSCOPY_MAX_LEN,
    GENOMICS_MAX_LEN,
    CLINICAL_FEATURE_DIM,
    DatasetSpec,
)


class BiofilmDataset(Dataset):
    """
    PyTorch Dataset for multimodal biofilm detection.

    Arguments:
        spec: DatasetSpec with paths and split parameters.
        split: One of 'train', 'val', 'test', or None for all.
        transform: Optional callable for image augmentations.
        demo_mode: If True (default), the dataset reports that no
                   real data is available.
        data_available: If False, the dataset will raise a clear
                        message that no data has been loaded.

    The dataset loads samples lazily — only the metadata CSV is read
    at construction.  Actual file I/O happens during __getitem__.
    """

    def __init__(
        self,
        spec: Optional[DatasetSpec] = None,
        split: Optional[str] = None,
        transform=None,
        demo_mode: bool = True,
        data_available: bool = False,
    ):
        super().__init__()
        self.spec = spec or DatasetSpec()
        self.split = split
        self.transform = transform
        self.demo_mode = demo_mode
        self.data_available = data_available
        self.samples: List[Dict] = []
        self.stats: Dict = {}

        if not data_available:
            warnings.warn("NO REAL DATASET AVAILABLE — dataset is empty.")
            return

        if not os.path.isfile(self.metadata_path):
            raise FileNotFoundError(
                f"Metadata CSV not found at {self.metadata_path}. "
                "See schema.py for the required format."
            )

        self._load_metadata()

    # ── Properties ─────────────────────────────────────────────────────

    @property
    def root(self) -> str:
        return self.spec.dataset_root

    @property
    def metadata_path(self) -> str:
        return os.path.join(self.root, self.spec.metadata_csv)

    def __len__(self) -> int:
        if not self.data_available:
            return 0
        return len(self.samples)

    def __getitem__(self, idx: int) -> Dict:
        """
        Return a single multimodal sample as a dict.

        Keys match MultimodalModel.forward() arguments:
            microscopy: (3, H, W) tensor or None / all-zero mask
            spectroscopy: (seq_len, 2) tensor or None
            genomics: (seq_len,) long tensor or None
            clinical: (CLINICAL_FEATURE_DIM,) tensor or None
            modality_mask: Dict[str, bool] indicating availability
            sample_id: str
            labels: float tensor (1,) or None for unlabelled samples
        """
        if not self.data_available or idx >= len(self.samples):
            raise IndexError("No data available — dataset is empty.")

        sample = self.samples[idx]
        sample_id = sample[SAMPLE_ID_COL]
        item: Dict = {"sample_id": sample_id, "labels": self._get_label(sample)}
        item["modality_mask"] = {}

        # ── Microscopy ──────────────────────────────────────────────
        micro_path = self._modality_path(sample, MICROSCOPY_PATH_COL, "microscopy")
        if micro_path and os.path.isfile(micro_path):
            from ..preprocessing.microscopy import preprocess_microscopy
            img_tensor = preprocess_microscopy(_read_bytes(micro_path))
            if img_tensor is not None:
                item["microscopy"] = img_tensor.squeeze(0)  # (C,H,W)
                item["modality_mask"]["microscopy"] = True

        # ── Spectrosopy ─────────────────────────────────────────────
        spec_path = self._modality_path(sample, SPECTROSCOPY_PATH_COL, "spectroscopy")
        if spec_path and os.path.isfile(spec_path):
            from ..preprocessing.spectroscopy import preprocess_spectroscopy
            spec_tensor = preprocess_spectroscopy(_read_bytes(spec_path))
            if spec_tensor is not None:
                item["spectroscopy"] = spec_tensor.squeeze(0)  # (seq_len, 2)
                item["modality_mask"]["spectroscopy"] = True

        # ── Genoics ─────────────────────────────────────────────────
        gen_path = self._modality_path(sample, GENOMICS_PATH_COL, "genomics")
        if gen_path and os.path.isfile(gen_path):
            from ..preprocessing.genomics import preprocess_genomics
            result = preprocess_genomics(_read_bytes(gen_path))
            if result is not None:
                indices, mask = result
                item["genomics"] = indices.squeeze(0)  # (seq_len,)
                item["genomics_mask"] = mask.squeeze(0)  # (seq_len,)
                item["modality_mask"]["genomics"] = True

        # ── Clinical ────────────────────────────────────────────────
        clin_feat = self._extract_clinical(sample)
        if clin_feat is not None:
            item["clinical"] = clin_feat.squeeze(0)  # (CLINICAL_FEATURE_DIM,)
            item["modality_mask"]["clinical"] = True

        return item

    # ── Internal helpers ───────────────────────────────────────────────

    def _load_metadata(self):
        """Load and filter the metadata CSV."""
        import pandas as pd

        df = pd.read_csv(self.metadata_path)

        # Filter by split if requested
        if self.split and SPLIT_COL in df.columns:
            df = df[df[SPLIT_COL].str.strip().str.lower() == self.split.lower()]

        self.samples = df.to_dict(orient="records")
        self.stats = self._compute_stats(df)

    def _compute_stats(self, df) -> Dict:
        """Compute basic statistics over the DataFrame."""
        stats = {}
        stats["total"] = len(df)
        if LABEL_COL in df.columns:
            stats["positive"] = int(df[LABEL_COL].sum())
            stats["negative"] = int((1 - df[LABEL_COL]).sum())
        for col, name, _ in self._modality_columns():
            if col in df.columns:
                present = df[col].notna() & df[col].astype(str).str.strip().ne("")
                stats[f"{name}_available"] = int(present.sum())
        return stats

    def _get_label(self, sample: Dict) -> Optional[torch.Tensor]:
        """Return the label tensor or None."""
        val = sample.get(LABEL_COL)
        if val is not None and str(val).strip():
            try:
                return torch.tensor([float(val)], dtype=torch.float32)
            except (ValueError, TypeError):
                pass
        return None

    def _modality_path(self, sample: Dict, col: str, subdir: str) -> Optional[str]:
        """Resolve the full path to a modality file."""
        val = sample.get(col)
        if val is not None and str(val).strip():
            rel = str(val).strip()
            # If it's just a filename, assume it's in the modality directory
            if os.sep not in rel and "/" not in rel:
                rel = os.path.join(subdir, rel)
            return os.path.join(self.root, rel)
        return None

    @staticmethod
    def _modality_columns() -> List[Tuple[str, str, List[str]]]:
        """Return (column, name, extensions) for each modality."""
        return [
            (MICROSCOPY_PATH_COL, "microscopy", MICROSCOPY_EXTENSIONS),
            (SPECTROSCOPY_PATH_COL, "spectroscopy", SPECTROSCOPY_EXTENSIONS),
            (GENOMICS_PATH_COL, "genomics", GENOMICS_EXTENSIONS),
            (CLINICAL_PATH_COL, "clinical", [".json"]),
        ]

    def _extract_clinical(self, sample: Dict) -> Optional[torch.Tensor]:
        """Build the clinical feature vector."""
        # Check if all flat columns exist
        flat = {c: sample.get(c) for c in CLINICAL_FEATURE_COLS}
        if all(v is not None for v in flat.values()):
            from ..clinical_encoder import encode_clinical_features
            return encode_clinical_features(flat)

        # Try loading from a JSON file
        clin_path = self._modality_path(sample, CLINICAL_PATH_COL, "clinical")
        if clin_path and os.path.isfile(clin_path):
            try:
                with open(clin_path, "r") as f:
                    clin_data = json.load(f)
                from ..clinical_encoder import encode_clinical_features
                return encode_clinical_features(clin_data)
            except (json.JSONDecodeError, Exception):
                pass

        return None


def _read_bytes(path: str) -> bytes:
    """Read a file as bytes."""
    with open(path, "rb") as f:
        return f.read()

class DatasetLoader(BiofilmDataset):
    """
    Legacy DatasetLoader (formerly in dataset_loader.py).

    A thin alias of BiofilmDataset kept for backwards compatibility.
    The canonical strict-layout loader is now BiofilmDataset, and the
    genomic experiment is loaded via GenomicExperimentLoader in
    dataset_loader.py (which is torch-free).
    """

    pass
