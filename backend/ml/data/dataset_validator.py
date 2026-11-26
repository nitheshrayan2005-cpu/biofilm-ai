#!/usr/bin/env python3
"""
BiofilmAI Data — Dataset Validator (genomic experiment)
==========================================================

Validates the S. epidermidis genomic dataset (Excel metadata + FASTA
genomes) and produces:

  - a dataset audit report (JSON)
  - a machine-readable dataset manifest (JSON)
  - isolate-level train/val/test splits (saved to disk)

Runtime checks performed by the loader/validator:
  - every metadata isolate has a FASTA file
  - every FASTA file maps to a metadata isolate
  - no isolate is duplicated (metadata or FASTA)
  - sequences are valid FASTA
  - required metadata fields exist
  - missing values are reported

Target: Epidemiology = pathogenic vs commensal (binary classification).
Input:  genome sequence ONLY. Epidemiology is the label and is never
        used as a model input feature.

Usage:
    python -m backend.ml.data.dataset_validator \
        --metadata path/to/metadata.xlsx \
        --fasta path/to/seq_dir_or.zip \
        [--out-dir ./experiment_audit] \
        [--seed 42]
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from .dataset_loader import GenomicExperimentLoader


def validate_experiment(
    metadata_path: str,
    fasta_source: str,
    seed: int = 42,
) -> GenomicExperimentLoader:
    """
    Run the full validation pipeline and return the loader with results.

    Raises nothing — errors are collected in `loader.errors` so the
    caller can report them.
    """
    loader = GenomicExperimentLoader(
        metadata_path=metadata_path,
        fasta_source=fasta_source,
        seed=seed,
    )
    loader.load()
    return loader


def write_outputs(loader: GenomicExperimentLoader, out_dir: str):
    """Write audit report, manifest, and splits to disk (machine-readable)."""
    os.makedirs(out_dir, exist_ok=True)

    audit = loader.audit()
    with open(os.path.join(out_dir, "dataset_audit.json"), "w") as f:
        json.dump(audit, f, indent=2)

    manifest = {
        "sample_count": loader.manifest.sample_count if loader.manifest else 0,
        "fasta_file_count": loader.manifest.fasta_file_count if loader.manifest else 0,
        "matched_sample_count": loader.manifest.matched_sample_count if loader.manifest else 0,
        "unmatched_sample_count": loader.manifest.unmatched_sample_count if loader.manifest else 0,
        "metadata_columns": loader.manifest.metadata_columns if loader.manifest else [],
        "label_distribution": loader.manifest.label_distribution if loader.manifest else {},
        "missing_value_summary": loader.manifest.missing_value_summary if loader.manifest else {},
        "sequence_length_statistics": loader.manifest.sequence_length_statistics if loader.manifest else {},
        "split_counts": loader.manifest.split_counts if loader.manifest else {},
    }
    with open(os.path.join(out_dir, "dataset_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    with open(os.path.join(out_dir, "splits.json"), "w") as f:
        json.dump(loader.splits, f, indent=2)

    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Validate the S. epidermidis genomic dataset"
    )
    parser.add_argument("--metadata", required=True, help="Path to the Excel metadata file")
    parser.add_argument("--fasta", required=True, help="Path to FASTA directory or seq.zip")
    parser.add_argument("--out-dir", default="./experiment_audit")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not os.path.isfile(args.metadata):
        print("NO REAL DATASET AVAILABLE — metadata file not found.")
        print(f"Expected: {args.metadata}")
        sys.exit(1)

    loader = validate_experiment(args.metadata, args.fasta, seed=args.seed)

    fasta_absent = not os.path.isdir(args.fasta) and not os.path.isfile(args.fasta)
    if fasta_absent:
        print(f"NOTE: FASTA source not found at {args.fasta} — genomic "
              "checks (sequence stats, isolate matching) are reported as unavailable.")
        loader.errors.append(
            f"FASTA source not found: {args.fasta}. "
            "Provide seq.zip or a FASTA directory to complete the genomic audit."
        )

    manifest = write_outputs(loader, args.out_dir)

    print("=" * 64)
    print("BiofilmAI Genomic Dataset — Validation & Audit")
    print("=" * 64)
    audit = loader.audit()
    print(f"  Total samples           : {audit['total_samples']}")
    print(f"  Pathogenic              : {audit['pathogenic_count']}")
    print(f"  Commensal               : {audit['commensal_count']}")
    print(f"  Class balance ratio     : {audit['class_balance_ratio']}")
    print(f"  Sequence length stats   : {audit['sequence_length_statistics']}")
    print(f"  Duplicate metadata IDs  : {audit['duplicate_check']['duplicate_isolate_ids_in_metadata']}")
    print(f"  Duplicate FASTA IDs     : {audit['duplicate_check']['duplicate_fasta_ids']}")
    print(f"  Isolates matched        : {audit['isolate_matching_check']['matched']}")
    print(f"  Isolates unmatched      : {audit['isolate_matching_check']['unmatched']}")
    print(f"  Splits (isolate-level)  : {audit['split_counts']}")
    print("-" * 64)
    if loader.errors:
        print("  ERRORS:")
        for e in loader.errors:
            print(f"    - {e}")
    else:
        print("  ✅ Dataset validation passed — no errors.")
    print("=" * 64)
    print(f"Artifacts written to: {os.path.abspath(args.out_dir)}")
    print("  dataset_audit.json · dataset_manifest.json · splits.json")


if __name__ == "__main__":
    main()
