"""
BiofilmAI Data — Dataset Checks
=================================

Implements the 10 validation rules checked by `validate_dataset.py`:

  1. unique sample_id
  2. valid modality file formats
  3. clinical data schema
  4. valid numeric spectroscopy
  5. valid genomic sequence
  6. readable microscopy image
  7. valid biofilm label
  8. duplicate detection
  9. missing-modality reporting
 10. sample-level splitting (handled by validate_dataset.py)

Each check is a pure function that appends errors/warnings to a report.
No biological data is created here — these are structural checks only.
"""

from __future__ import annotations

import json
import os
from typing import Dict, List

from .dataset_schema import (
    CLINICAL_SCHEMA,
    CLINICAL_REQUIRED_FIELDS,
    MICROSCOPY_EXTENSIONS,
    SPECTROSCOPY_EXTENSIONS,
    GENOMICS_EXTENSIONS,
    DatasetSpec,
)
from .modality_alignment import MODALITY_SPECS, missing_modalities


def run_all_checks(
    records: List[dict],
    dataset_root: str,
    spec: DatasetSpec,
) -> Dict:
    """Run all structural checks and return a merged report dict."""
    report: Dict = {
        "errors": [],
        "warnings": [],
        "valid_samples": 0,
        "invalid_samples": 0,
        "invalid_samples_list": [],
        "duplicate_samples": [],
        "invalid_labels": [],
        "missing_modalities": {},
    }

    # 1 & 8 — unique sample_ids / duplicates
    _check_duplicates(records, report)

    for rec in records:
        sid = rec.get("sample_id", "")
        sample_errors: List[str] = []

        # 2 — valid formats
        for modality, (col, exts) in MODALITY_SPECS.items():
            path = rec.get(f"{modality}_path")
            if not path:
                continue  # handled by missing-modality reporting
            ext = os.path.splitext(path)[1].lower()
            if ext not in exts:
                sample_errors.append(f"{modality}: invalid extension '{ext}' (allowed {exts})")

        # 3 — clinical schema
        clinical = rec.get("clinical_data")
        if clinical is None and rec.get("clinical_path"):
            clinical = _read_json(rec["clinical_path"])
        if clinical is not None:
            _check_clinical(clinical, sid, report, sample_errors)

        # 4 — spectroscopy numeric content
        if rec.get("spectroscopy_path"):
            if not _check_spectroscopy(rec["spectroscopy_path"]):
                sample_errors.append("spectroscopy: no valid numeric wavelength/intensity pairs")

        # 5 — genomics sequence validity
        if rec.get("genomics_path"):
            if not _check_genomics(rec["genomics_path"]):
                sample_errors.append("genomics: no valid nucleotide sequence found")

        # 6 — microscopy readable image
        if rec.get("microscopy_path"):
            if not _check_microscopy(rec["microscopy_path"]):
                sample_errors.append("microscopy: file is not a readable image")

        # 7 — valid label
        label = rec.get("label")
        if label is None:
            report["invalid_labels"].append(f"{sid}: missing or invalid label")
            sample_errors.append("label: missing or invalid (expected 0 or 1)")

        if sample_errors:
            report["invalid_samples"] += 1
            report["invalid_samples_list"].append({"sample_id": sid, "errors": sample_errors})
        else:
            report["valid_samples"] += 1

    # 9 — missing modalities (reported, never fabricated)
    report["missing_modalities"] = missing_modalities(records)

    return report


# ── Individual checks ───────────────────────────────────────────────────────

def _check_duplicates(records: List[dict], report: Dict):
    seen: Dict[str, int] = {}
    for rec in records:
        sid = rec.get("sample_id", "")
        seen[sid] = seen.get(sid, 0) + 1
    dups = {sid: n for sid, n in seen.items() if n > 1}
    if dups:
        report["duplicate_samples"].extend(dups.keys())
        report["errors"].append(f"Duplicate sample_ids detected: {dups}")


def _check_clinical(clinical: dict, sid: str, report: Dict, sample_errors: List[str]):
    if not isinstance(clinical, dict):
        sample_errors.append("clinical: expected a JSON object")
        return
    for field in CLINICAL_REQUIRED_FIELDS:
        if field not in clinical or clinical[field] in (None, ""):
            sample_errors.append(f"clinical: missing required field '{field}'")
            continue
        expected = CLINICAL_SCHEMA.get(field, "")
        if expected == "number" and not isinstance(clinical[field], (int, float)):
            sample_errors.append(f"clinical: '{field}' must be a number")
        if expected == "bool" and not isinstance(clinical[field], bool):
            sample_errors.append(f"clinical: '{field}' must be a boolean")


def _check_spectroscopy(path: str) -> bool:
    """Confirm the file contains at least one valid numeric pair."""
    try:
        with open(path, "r") as f:
            for line in f:
                parts = line.replace(",", " ").replace(";", " ").split()
                if len(parts) >= 2:
                    try:
                        float(parts[0])
                        float(parts[1])
                        return True
                    except ValueError:
                        continue
        return False
    except OSError:
        return False


def _check_genomics(path: str) -> bool:
    """Confirm the file contains valid nucleotide characters."""
    valid = set("ACGTUacgtu")
    try:
        with open(path, "r") as f:
            content = f.read()
        lines = [l for l in content.splitlines() if not l.startswith(">")]
        sequence = "".join(lines)
        if not sequence.strip():
            return False
        # Allow at least 80% valid nucleotides
        valid_count = sum(1 for c in sequence if c in valid)
        return valid_count / len(sequence) >= 0.8
    except OSError:
        return False


def _check_microscopy(path: str) -> bool:
    """Confirm the file can be opened as an image."""
    try:
        from PIL import Image

        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def _read_json(path: str) -> dict:
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return {}
