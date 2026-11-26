"""
BiofilmAI Data — Dataset Validator
====================================

Validates a real dataset against the schema specification.
Reports structural issues, missing files, duplicates, class imbalance,
and potential data leakage.

If no real dataset is present, clearly reports:
    "NO REAL DATASET AVAILABLE — MODEL REMAINS IN DEMO MODE."
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .schema import (
    SAMPLE_ID_COL,
    LABEL_COL,
    SPLIT_COL,
    MICROSCOPY_PATH_COL,
    SPECTROSCOPY_PATH_COL,
    GENOMICS_PATH_COL,
    CLINICAL_PATH_COL,
    MICROSCOPY_EXTENSIONS,
    SPECTROSCOPY_EXTENSIONS,
    GENOMICS_EXTENSIONS,
    DatasetSpec,
)


class DatasetValidator:
    """
    Validates a dataset directory against the BiofilmAI schema.

    Usage:
        validator = DatasetValidator("/path/to/dataset")
        report = validator.validate()
        for issue in report["issues"]:
            print(issue)
    """

    MODALITY_CONFIGS: List[Tuple[str, str, List[str]]] = [
        (MICROSCOPY_PATH_COL, "microscopy", MICROSCOPY_EXTENSIONS),
        (SPECTROSCOPY_PATH_COL, "spectroscopy", SPECTROSCOPY_EXTENSIONS),
        (GENOMICS_PATH_COL, "genomics", GENOMICS_EXTENSIONS),
        (CLINICAL_PATH_COL, "clinical", [".json"]),
    ]

    def __init__(self, dataset_root: str, spec: Optional[DatasetSpec] = None):
        self.root = dataset_root
        self.spec = spec or DatasetSpec(dataset_root=dataset_root)
        self.df: Optional[pd.DataFrame] = None
        self.report: Dict = {
            "dataset_path": dataset_root,
            "available": os.path.isdir(dataset_root),
            "total_samples": 0,
            "samples_with_microscopy": 0,
            "samples_with_spectroscopy": 0,
            "samples_with_genomics": 0,
            "samples_with_clinical": 0,
            "complete_multimodal": 0,
            "positive_labels": 0,
            "negative_labels": 0,
            "missing_modalities": 0,
            "duplicate_sample_ids": 0,
            "invalid_files": [],
            "possible_data_leakage": False,
            "class_imbalance_ratio": None,
            "issues": [],
            "warnings": [],
            "errors": [],
        }

    def validate(self) -> Dict:
        """Run all validation checks. Returns a structured report dict."""
        self.report["available"] = os.path.isdir(self.root)

        if not self.report["available"]:
            self.report["issues"].append(
                "NO REAL DATASET AVAILABLE — MODEL REMAINS IN DEMO MODE."
            )
            return self.report

        # Check metadata CSV
        meta_path = os.path.join(self.root, self.spec.metadata_csv)
        if not os.path.isfile(meta_path):
            self.report["errors"].append(
                f"Metadata CSV not found at {meta_path}. "
                f"Expected filename: {self.spec.metadata_csv}"
            )
            return self.report

        try:
            self.df = pd.read_csv(meta_path)
        except Exception as e:
            self.report["errors"].append(f"Cannot read metadata CSV: {e}")
            return self.report

        self._check_required_columns()
        self._check_sample_ids()
        self._check_labels()
        self._check_modalities()
        self._check_splits()
        self._check_leakage()
        self._summarize()

        return self.report

    def _check_required_columns(self):
        if SAMPLE_ID_COL not in self.df.columns:
            self.report["errors"].append(
                f"Required column '{SAMPLE_ID_COL}' not found in metadata CSV."
            )

    def _check_sample_ids(self):
        if SAMPLE_ID_COL not in self.df.columns:
            return
        ids = self.df[SAMPLE_ID_COL].astype(str).str.strip()
        duplicates = ids[ids.duplicated()]
        count = len(duplicates)
        self.report["duplicate_sample_ids"] = count
        if count > 0:
            self.report["errors"].append(
                f"Found {count} duplicate sample IDs: {duplicates.unique().tolist()}"
            )

    def _check_labels(self):
        if LABEL_COL not in self.df.columns:
            self.report["warnings"].append(
                f"Label column '{LABEL_COL}' not found. "
                "Samples treated as unlabelled (inference only)."
            )
            return

        labels = self.df[LABEL_COL]
        unique = labels.dropna().unique()
        invalid = set(unique) - {0, 1}
        if invalid:
            self.report["errors"].append(
                f"Invalid label values: {invalid}. Must be 0 or 1"
            )

        self.report["positive_labels"] = int(labels.dropna().sum())
        self.report["negative_labels"] = int((1 - labels.dropna()).sum())

        pos = self.report["positive_labels"]
        neg = self.report["negative_labels"]
        if pos > 0 and neg > 0:
            ratio = max(pos, neg) / min(pos, neg)
            self.report["class_imbalance_ratio"] = round(ratio, 2)
            if ratio > 5:
                self.report["warnings"].append(
                    f"Severe class imbalance: {ratio:.1f}:1 "
                    f"(positive={pos}, negative={neg})"
                )
        elif pos == 0 and neg > 0:
            self.report["warnings"].append("No positive samples found.")
        elif neg == 0 and pos > 0:
            self.report["warnings"].append("No negative samples found.")
        else:
            self.report["warnings"].append("No labelled samples found at all.")

    def _check_modalities(self):
        for col, name, exts in self.MODALITY_CONFIGS:
            if col not in self.df.columns:
                continue

            paths = self.df[col].dropna().astype(str).str.strip()
            paths = paths[paths.ne("")]

            self.report[f"samples_with_{name}"] = len(paths)

            for p in paths:
                full_path = os.path.join(self.root, p)
                if not os.path.isfile(full_path):
                    self.report["invalid_files"].append(full_path)

                ext = os.path.splitext(p)[1].lower()
                if ext not in exts:
                    self.report["invalid_files"].append(
                        f"{p}: unsupported extension '{ext}'. "
                        f"Expected: {exts}"
                    )

        # Count complete multimodal samples
        mask_cols = []
        for col, name, _ in self.MODALITY_CONFIGS:
            if col in self.df.columns:
                mask_cols.append(col)

        if mask_cols and self.df is not None:
            available = self.df[mask_cols].notna()
            complete = available.all(axis=1)
            self.report["complete_multimodal"] = int(complete.sum())
            missing = self.df[mask_cols].isna().sum().sum()
            self.report["missing_modalities"] = int(missing)

    def _check_splits(self):
        if SPLIT_COL not in self.df.columns:
            return
        splits = self.df[SPLIT_COL].str.strip().str.lower()
        counts = splits.value_counts()
        for split_name in ["train", "val", "test"]:
            if split_name not in counts:
                self.report["warnings"].append(
                    f"No '{split_name}' split found in dataset."
                )

    def _check_leakage(self):
        if self.report["duplicate_sample_ids"] > 0:
            self.report["possible_data_leakage"] = True
        if SPLIT_COL in self.df.columns:
            splits = self.df[SPLIT_COL].str.strip().str.lower()
            if len(splits.unique()) == 1:
                self.report["warnings"].append(
                    f"All samples in a single split '{splits.unique()[0]}'. "
                    "No train/val/test separation."
                )
                self.report["possible_data_leakage"] = True

    def _summarize(self):
        self.report["total_samples"] = len(self.df) if self.df is not None else 0
        errors = self.report.get("errors", [])
        warnings = self.report.get("warnings", [])
        self.report["issues"].extend(errors)
        self.report["issues"].extend(warnings)
        if not errors and self.report["available"]:
            self.report["issues"].append(
                "DATASET VALIDATION COMPLETE — Structure is compatible."
            )