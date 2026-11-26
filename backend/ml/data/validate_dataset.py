#!/usr/bin/env python3
"""
BiofilmAI Data — Dataset Validation Script
=============================================

CLI entry point that validates a real dataset against the strict schema
and produces a clear validation report.

Usage:
    python -m backend.ml.data.validate_dataset ./dataset
    python -m backend.ml.data.validate_dataset ./dataset --json

If no dataset exists, reports:
    "NO REAL DATASET AVAILABLE — MODEL REMAINS IN DEMO MODE."

The validator performs these checks:
  1. Every sample has a unique sample_id
  2. Required modality files have valid formats
  3. Clinical data follows the expected schema
  4. Spectroscopy data contains valid numeric wavelength/intensity
  5. Genomics data is valid sequence/features
  6. Microscopy files are readable images
  7. The biofilm label is valid
  8. Duplicate samples are detected
  9. Missing modalities are reported (never fabricated)
 10. Train/val/test splitting is performed at the SAMPLE level
"""

from __future__ import annotations

import argparse
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Validate a BiofilmAI dataset directory")
    parser.add_argument(
        "dataset_root",
        type=str,
        nargs="?",
        default="dataset",
        help="Path to the dataset directory (default: ./dataset)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the validation report as JSON",
    )
    args = parser.parse_args()

    dataset_root = os.path.abspath(args.dataset_root)

    # ── Import data modules (lazy — no torch required for validation) ────
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
    from backend.ml.data.dataset_schema import DatasetSpec
    from backend.ml.data.modality_alignment import (
        build_manifest,
        check_alignment,
        missing_modalities,
        split_samples,
    )
    from backend.ml.data.dataset_checks import run_all_checks

    spec = DatasetSpec(dataset_root=dataset_root)

    # ── No dataset present ────────────────────────────────────────────────
    if not os.path.isdir(dataset_root):
        report = {
            "dataset_path": dataset_root,
            "available": False,
            "status": "NO REAL DATASET AVAILABLE — MODEL REMAINS IN DEMO MODE.",
            "valid_samples": 0,
            "invalid_samples": 0,
            "missing_modalities": [],
            "duplicate_samples": [],
            "invalid_labels": [],
            "split_counts": {},
        }
        _emit(report, args.json)
        return

    # ── Build manifest / alignment ────────────────────────────────────────
    try:
        records = build_manifest(dataset_root, spec)
    except Exception as exc:
        report = {
            "dataset_path": dataset_root,
            "available": True,
            "status": f"MANIFEST ERROR: {exc}",
            "valid_samples": 0,
            "invalid_samples": 0,
            "missing_modalities": [],
            "duplicate_samples": [],
            "invalid_labels": [],
            "split_counts": {},
        }
        _emit(report, args.json)
        return

    # ── Run all 10 checks ─────────────────────────────────────────────────
    report = run_all_checks(records, dataset_root, spec)

    # ── Sample-level split counts ─────────────────────────────────────────
    try:
        splits = split_samples(records, spec)
        report["split_counts"] = {
            "train": len(splits["train"]),
            "val": len(splits["val"]),
            "test": len(splits["test"]),
            "total": len(records),
            "level": "sample",  # leakage prevention
        }
    except Exception as exc:
        report["split_counts"] = {"error": str(exc)}

    report["dataset_path"] = dataset_root
    report["available"] = True
    report["status"] = "VALID" if not report["errors"] else "INVALID"

    _emit(report, args.json)


def _emit(report: dict, as_json: bool):
    if as_json:
        print(json.dumps(report, indent=2))
        return

    print("=" * 64)
    print("BiofilmAI Dataset Validation Report")
    print("=" * 64)
    print(f"Dataset path : {report.get('dataset_path', '')}")
    print(f"Status       : {report.get('status', '')}")
    print("-" * 64)
    print(f"  Valid samples      : {report.get('valid_samples', 0)}")
    print(f"  Invalid samples    : {report.get('invalid_samples', 0)}")
    print(f"  Duplicate samples  : {len(report.get('duplicate_samples', []))}")
    print(f"  Invalid labels     : {len(report.get('invalid_labels', []))}")
    print("-" * 64)

    missing = report.get("missing_modalities", {})
    if isinstance(missing, dict) and missing:
        print("  Missing modalities (reported, NOT fabricated):")
        for mod, samples in missing.items():
            print(f"    - {mod}: {len(samples)} samples missing")
    elif isinstance(missing, list) and missing:
        print(f"  Missing modality entries: {len(missing)}")

    print("-" * 64)
    print("  Split counts (sample level, leakage-safe):")
    for key, value in report.get("split_counts", {}).items():
        print(f"    {key:8s}: {value}")
    print("-" * 64)

    if report.get("errors"):
        print("  ERRORS:")
        for e in report["errors"]:
            print(f"    - {e}")
    if report.get("warnings"):
        print("  WARNINGS:")
        for w in report["warnings"]:
            print(f"    - {w}")

    if report.get("status") == "VALID":
        print("  ✅ DATASET VALIDATION COMPLETE — Structure is compatible.")
    elif "NO REAL DATASET" in str(report.get("status", "")):
        print("  (no dataset present — nothing to validate; DEMO MODE remains active.)")
    else:
        print("  ❌ DATASET HAS ERRORS — fix them before training.")
    print("=" * 64)


if __name__ == "__main__":
    main()
