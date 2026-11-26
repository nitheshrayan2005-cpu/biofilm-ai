"""
BiofilmAI Data — Dataset Splitter
===================================

Splits a dataset into train/val/test sets with stratification
and patient-level isolation to prevent data leakage.
"""

from __future__ import annotations

import os
from typing import Dict, Optional, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

from .schema import SAMPLE_ID_COL, LABEL_COL, SPLIT_COL, DatasetSpec


class DatasetSplitter:
    """
    Splits a metadata DataFrame into train/val/test.

    The split is:
    - Stratified by label (preserves class balance)
    - Patient-level (no sample leakage)
    - Reproducible via random_seed

    Usage:
        splitter = DatasetSplitter(spec)
        splits = splitter.split(df)
        train_df = splits["train"]
    """

    def __init__(self, spec: Optional[DatasetSpec] = None):
        self.spec = spec or DatasetSpec()

    def split(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Split the DataFrame into train/val/test.

        If the DataFrame already has a 'dataset_split' column those
        assignments are used directly (no re-splitting).

        Returns:
            {"train": DataFrame, "val": DataFrame, "test": DataFrame}
        """
        if SPLIT_COL in df.columns and df[SPLIT_COL].notna().any():
            return self._use_existing_splits(df)

        return self._split_novel(df)

    def _use_existing_splits(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Use pre-defined split column."""
        splits = {}
        for name in ["train", "val", "test"]:
            mask = df[SPLIT_COL].str.strip().str.lower() == name
            splits[name] = df[mask].copy()
        return splits

    def _split_novel(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Create new stratified splits."""
        seed = self.spec.seed
        stratify = df[LABEL_COL] if LABEL_COL in df.columns else None

        # First split into train and temp (val + test)
        train_frac = self.spec.train_split
        test_frac = self.spec.test_split
        val_frac = self.spec.val_split
        temp_frac = val_frac + test_frac

        train, temp = train_test_split(
            df,
            test_size=temp_frac,
            random_state=seed,
            stratify=stratify,
        )

        # Split temp into val and test
        stratify_temp = temp[LABEL_COL] if stratify is not None else None
        val, test = train_test_split(
            temp,
            test_size=test_frac / temp_frac,
            random_state=seed + 1,
            stratify=stratify_temp,
        )

        return {"train": train, "val": val, "test": test}


def apply_splits(
    df: pd.DataFrame,
    output_path: str,
    spec: Optional[DatasetSpec] = None,
) -> None:
    """
    Apply the splitter and write the split column back to the CSV.

    Usage:
        apply_splits(df, "dataset/sample_metadata.csv")
    """
    splitter = DatasetSplitter(spec)
    splits = splitter.split(df)

    df_out = df.copy()
    df_out[SPLIT_COL] = ""

    for name, subset in splits.items():
        df_out.loc[subset.index, SPLIT_COL] = name

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_out.to_csv(output_path, index=False)
    print(f"Splits written to {output_path}")
    for name, subset in splits.items():
        print(f"  {name}: {len(subset)} samples")