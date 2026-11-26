"""
BiofilmAI Data — Modality Alignment
=====================================

Ensures modality files are aligned to the same samples and that missing
modalities are detected (never fabricated).

Responsibilities:
  1. Build a manifest from the dataset directory (or read manifest.csv)
  2. Verify every referenced modality file exists and has a valid extension
  3. Detect which modalities are missing per sample
  4. Perform SAMPLE-LEVEL train/val/test splitting to prevent leakage
"""

from __future__ import annotations

import os
from typing import Dict, List, Optional

from .dataset_schema import (
    SAMPLE_ID_COL,
    MICROSCOPY_COL,
    SPECTROSCOPY_COL,
    GENOMICS_COL,
    CLINICAL_COL,
    LABEL_COL,
    SPLIT_COL,
    MANIFEST_COLUMNS,
    MICROSCOPY_EXTENSIONS,
    SPECTROSCOPY_EXTENSIONS,
    GENOMICS_EXTENSIONS,
    CLINICAL_EXTENSIONS,
    MODALITY_SUBDIRS,
    LABEL_FILENAME,
    DatasetSpec,
)

# modality name → (manifest column, accepted extensions)
MODALITY_SPECS: Dict[str, tuple] = {
    "microscopy": (MICROSCOPY_COL, MICROSCOPY_EXTENSIONS),
    "spectroscopy": (SPECTROSCOPY_COL, SPECTROSCOPY_EXTENSIONS),
    "genomics": (GENOMICS_COL, GENOMICS_EXTENSIONS),
    "clinical": (CLINICAL_COL, CLINICAL_EXTENSIONS),
}


def build_manifest(dataset_root: str, spec: Optional[DatasetSpec] = None) -> List[dict]:
    """
    Build a list of sample records from the dataset directory.

    Layout detection:
      - If <root>/manifest.csv exists → read it (manifest layout)
      - Else if <root>/sample_metadata.csv exists → read it (flat layout)
      - Else → scan per-sample directories: <root>/sample_<id>/{modality}/

    Each record: {sample_id, microscopy_path, spectroscopy_path,
                  genomics_path, clinical_path, label, dataset_split?}
    Paths are absolute.
    """
    spec = spec or DatasetSpec(dataset_root=dataset_root)

    manifest_path = os.path.join(dataset_root, spec.manifest_file)
    if os.path.isfile(manifest_path):
        return _read_manifest_csv(manifest_path, dataset_root)

    flat_path = os.path.join(dataset_root, spec.metadata_csv)
    if os.path.isfile(flat_path):
        return _read_manifest_csv(flat_path, dataset_root, flat=True)

    return _scan_sample_dirs(dataset_root)


def _read_manifest_csv(path: str, dataset_root: str, flat: bool = False) -> List[dict]:
    import pandas as pd

    df = pd.read_csv(path)
    missing = [c for c in MANIFEST_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Manifest {path} is missing required columns: {missing}. "
            f"Expected: {MANIFEST_COLUMNS}"
        )

    records = []
    for _, row in df.iterrows():
        rec = {
            "sample_id": str(row[SAMPLE_ID_COL]).strip(),
            "microscopy_path": _abs(dataset_root, row.get(MICROSCOPY_COL)),
            "spectroscopy_path": _abs(dataset_root, row.get(SPECTROSCOPY_COL)),
            "genomics_path": _abs(dataset_root, row.get(GENOMICS_COL)),
            "clinical_path": _abs(dataset_root, row.get(CLINICAL_COL)),
            "label": _parse_label(row.get(LABEL_COL)),
        }
        if SPLIT_COL in df.columns:
            rec["dataset_split"] = str(row.get(SPLIT_COL)).strip().lower()
        records.append(rec)
    return records


def _scan_sample_dirs(dataset_root: str) -> List[dict]:
    """Scan <root>/sample_<id>/<modality>/... directories."""
    records = []
    for name in sorted(os.listdir(dataset_root)):
        sample_dir = os.path.join(dataset_root, name)
        if not os.path.isdir(sample_dir):
            continue
        sample_id = name
        rec: dict = {"sample_id": sample_id, "label": None}
        for modality, subdir in MODALITY_SUBDIRS.items():
            mod_dir = os.path.join(sample_dir, subdir)
            if os.path.isdir(mod_dir):
                files = sorted(
                    f for f in os.listdir(mod_dir)
                    if os.path.isfile(os.path.join(mod_dir, f))
                )
                rec[f"{modality}_path"] = os.path.join(mod_dir, files[0]) if files else None
            else:
                rec[f"{modality}_path"] = None

        label_path = os.path.join(sample_dir, LABEL_FILENAME)
        if os.path.isfile(label_path):
            with open(label_path, "r") as f:
                rec["label"] = _parse_label(f.read().strip())
        records.append(rec)
    return records


def check_alignment(records: List[dict]) -> Dict:
    """
    Verify alignment: every referenced file exists, has a valid extension,
    and belongs to exactly one sample_id.

    Returns a report dict with "errors" and "warnings".
    """
    report: Dict = {"errors": [], "warnings": [], "missing": [], "invalid": []}

    seen_ids: Dict[str, int] = {}
    for rec in records:
        sid = rec["sample_id"]
        seen_ids[sid] = seen_ids.get(sid, 0) + 1

        for modality, (col, exts) in MODALITY_SPECS.items():
            path = rec.get(f"{modality}_path")
            if not path:
                report["missing"].append(f"{sid}:{modality}")
                continue
            if not os.path.isfile(path):
                report["invalid"].append(f"{sid}:{modality}:file-not-found:{path}")
                continue
            ext = os.path.splitext(path)[1].lower()
            if ext not in exts:
                report["invalid"].append(f"{sid}:{modality}:bad-extension:{ext}")

    # Duplicate sample ids
    dups = {sid: n for sid, n in seen_ids.items() if n > 1}
    if dups:
        report["errors"].append(f"Duplicate sample_ids: {dups}")

    return report


def missing_modalities(records: List[dict]) -> Dict[str, List[str]]:
    """Return {modality: [sample_ids missing that modality]}."""
    missing: Dict[str, List[str]] = {m: [] for m in MODALITY_SPECS}
    for rec in records:
        for modality in MODALITY_SPECS:
            if not rec.get(f"{modality}_path"):
                missing[modality].append(rec["sample_id"])
    return missing


def split_samples(
    records: List[dict],
    spec: Optional[DatasetSpec] = None,
) -> Dict[str, List[dict]]:
    """
    Perform SAMPLE-LEVEL stratified splitting (train / val / test).

    If records already carry a `dataset_split` column those assignments
    are used verbatim (no re-split). Otherwise stratification by label
    is performed with a fixed seed to prevent data leakage.

    IMPORTANT: splitting is at the sample level — a sample and all of its
    modality files always stay in the same split.
    """
    spec = spec or DatasetSpec()

    # Use pre-assigned splits if present
    if any(rec.get("dataset_split") for rec in records):
        splits = {"train": [], "val": [], "test": []}
        for rec in records:
            s = rec.get("dataset_split", "")
            if s in splits:
                splits[s].append(rec)
        return splits

    # Stratified split by label (fall back to plain split if labels are
    # missing/invalid — the validator reports invalid labels separately)
    try:
        import pandas as pd
        from sklearn.model_selection import train_test_split
    except ImportError:  # pragma: no cover
        raise ImportError("pandas and scikit-learn are required for splitting")

    df = pd.DataFrame(records)
    stratify = df[LABEL_COL] if LABEL_COL in df.columns else None

    use_stratify = False
    if stratify is not None and not stratify.isna().any() and stratify.nunique() > 1:
        use_stratify = True

    temp_frac = spec.val_split + spec.test_split
    train, temp = train_test_split(
        df,
        test_size=temp_frac,
        random_state=spec.seed,
        stratify=stratify if use_stratify else None,
    )
    stratify_temp = temp[LABEL_COL] if use_stratify else None
    val, test = train_test_split(
        temp,
        test_size=spec.test_split / temp_frac,
        random_state=spec.seed + 1,
        stratify=stratify_temp,
    )

    return {
        "train": train.to_dict(orient="records"),
        "val": val.to_dict(orient="records"),
        "test": test.to_dict(orient="records"),
    }


def _abs(dataset_root: str, value) -> Optional[str]:
    """Convert a manifest-relative path to an absolute path.

    Handles NaN (pandas parses empty CSV cells as NaN) and empty strings
    as "modality genuinely missing" — they are never turned into paths.
    """
    if value is None:
        return None
    if isinstance(value, float) and value != value:  # NaN check
        return None
    if isinstance(value, str) and not value.strip():
        return None
    value = str(value).strip()
    if not value or value.lower() in ("nan", "none", "null"):
        return None
    if os.path.isabs(value):
        return value
    return os.path.join(dataset_root, value)


def _parse_label(value) -> Optional[int]:
    """Parse a biofilm label: 0 or 1; returns None if invalid."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        v = int(value)
        return v if v in (0, 1) else None
    s = str(value).strip().lower()
    if s in ("0", "0.0", "false", "no", "absent"):
        return 0
    if s in ("1", "1.0", "true", "yes", "present"):
        return 1
    return None
