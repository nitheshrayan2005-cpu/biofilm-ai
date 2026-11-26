"""
BiofilmAI Data — Dataset Loader
==================================

Loads the FIRST REAL EXPERIMENT: genomic pathogenic-vs-commensal
classification of S. epidermidis isolates.

Inputs:
  - Excel metadata file (one row per isolate, with an isolate ID column
    and an 'Epidemiology' target column: pathogenic / commensal)
  - a directory of FASTA genome files (or a seq.zip archive)

The loader:
  1. reads and normalizes the Excel metadata
  2. parses every FASTA genome file
  3. matches isolate IDs bidirectionally (metadata ↔ FASTA)
  4. verifies: every metadata isolate has a FASTA, every FASTA maps back,
     no duplicates, valid sequences, required fields present
  5. reports missing values
  6. builds a machine-readable manifest
  7. performs an isolate-level stratified train/val/test split

IMPORTANT: The 'Epidemiology' column is the TARGET (label). It must NOT be
used as a model input feature. Model input = genome sequence only.
"""

from __future__ import annotations

import os
import zipfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

from .fasta_parser import (
    FastaRecord,
    FastaStats,
    header_id,
    normalize_id,
    parse_fasta_file,
    sequence_is_valid,
)

# Default expected columns (auto-detected from actual file when possible)
DEFAULT_ID_COLUMNS = ["isolate_id", "isolate", "Isolate", "isolateID", "sample_id", "ID"]
DEFAULT_TARGET_COLUMNS = ["Epidemiology", "epidemiology", "Epidemiology_class", "category"]

POSITIVE_VALUES = {"pathogenic", "pathogen", "clinical", "positive", "1", "1.0", "yes", "true"}
NEGATIVE_VALUES = {"commensal", "commensal_skin", "carriage", "negative", "0", "0.0", "no", "false"}


@dataclass
class SampleRecord:
    """One isolate with its metadata, genome, and split assignment."""
    isolate_id: str
    epidemiology: Optional[str]
    label: Optional[int]               # 1 = pathogenic, 0 = commensal
    fasta_path: Optional[str]
    sequence_length: Optional[int]
    gc_content: Optional[float]
    metadata_fields: Dict = field(default_factory=dict)


@dataclass
class ExperimentManifest:
    """Machine-readable manifest of the loaded experiment."""
    sample_count: int
    fasta_file_count: int
    matched_sample_count: int
    unmatched_sample_count: int
    metadata_columns: List[str]
    label_distribution: Dict
    missing_value_summary: Dict
    sequence_length_statistics: Dict
    split_counts: Dict


class GenomicExperimentLoader:
    """
    Loader for the S. epidermidis genomic experiment.

    Args:
        metadata_path: path to the Excel metadata file
        fasta_source: directory of FASTA files OR a .zip archive containing them
        id_column: override for the isolate-ID column name
        target_column: override for the Epidemiology column name
        seed: random seed for the reproducible split
    """

    def __init__(
        self,
        metadata_path: str,
        fasta_source: str,
        id_column: Optional[str] = None,
        target_column: Optional[str] = None,
        seed: int = 42,
    ):
        self.metadata_path = metadata_path
        self.fasta_source = fasta_source
        self.id_column = id_column
        self.target_column = target_column
        self.seed = seed

        self.metadata_df: Optional[pd.DataFrame] = None
        self.records: List[SampleRecord] = []
        self.fasta_stats = FastaStats()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.manifest: Optional[ExperimentManifest] = None
        self.splits: Dict[str, List[str]] = {"train": [], "val": [], "test": []}

    # ── Main entry ────────────────────────────────────────────────────────

    def load(self) -> "GenomicExperimentLoader":
        """Run the full ingestion + validation + split pipeline."""
        self._read_metadata()
        fasta_records = self._read_fasta_files()
        self._match_isolates(fasta_records)
        self._build_split()
        self.manifest = self._build_manifest()
        return self

    # ── Step 1: metadata ──────────────────────────────────────────────────

    def _read_metadata(self):
        if not os.path.isfile(self.metadata_path):
            self.errors.append(f"Metadata file not found: {self.metadata_path}")
            return
        try:
            if self.metadata_path.lower().endswith((".csv", ".tsv", ".txt")):
                self.metadata_df = pd.read_csv(self.metadata_path)
            else:
                self.metadata_df = pd.read_excel(self.metadata_path)
        except Exception as exc:
            self.errors.append(f"Cannot read metadata file: {exc}")
            return

        self.id_column = self._resolve_column(
            DEFAULT_ID_COLUMNS, "isolate_id", required=True
        )
        self.target_column = self._resolve_column(
            DEFAULT_TARGET_COLUMNS, "Epidemiology", required=True
        )

        if self.id_column is None or self.target_column is None:
            return

        df = self.metadata_df.copy()
        df["_norm_id"] = df[self.id_column].map(
            lambda v: normalize_id(v) if pd.notna(v) else ""
        )

        for _, row in df.iterrows():
            raw_id = row.get(self.id_column)
            norm_id = row.get("_norm_id", "")
            epi = row.get(self.target_column)
            label = self._map_label(epi)
            record = SampleRecord(
                isolate_id=str(raw_id) if pd.notna(raw_id) else "",
                epidemiology=str(epi) if pd.notna(epi) else None,
                label=label,
                fasta_path=None,
                sequence_length=None,
                gc_content=None,
                metadata_fields={
                    col: (None if pd.isna(v) else v)
                    for col, v in row.items()
                    if col not in ("_norm_id",)
                },
            )
            record.metadata_fields["_norm_id"] = norm_id
            self.records.append(record)

    def _resolve_column(self, candidates: List[str], default: str, required: bool):
        if self.metadata_df is None:
            return None
        # Exact match first
        for cand in candidates:
            if cand in self.metadata_df.columns:
                return cand
        # Case-insensitive / whitespace-tolerant fallback
        norm = {str(c).strip().lower(): c for c in self.metadata_df.columns}
        for cand in candidates:
            if str(cand).strip().lower() in norm:
                return norm[str(cand).strip().lower()]
        if required:
            self.errors.append(
                f"Could not find a required column among {candidates} in the "
                f"metadata file (columns: {list(self.metadata_df.columns)})"
            )
            return None
        return default

    # ── Step 2: FASTA files ───────────────────────────────────────────────

    def _read_fasta_files(self) -> Dict[str, FastaRecord]:
        """Parse all FASTA files (from dir or zip). Returns {norm_id: record}."""
        files = self._enumerate_fasta_files()
        self.fasta_stats.file_count = len(files)
        fasta_by_id: Dict[str, FastaRecord] = {}

        for path in files:
            try:
                records = parse_fasta_file(path)
            except Exception as exc:
                self.fasta_stats.invalid_files.append(os.path.basename(path))
                self.errors.append(f"Invalid FASTA {os.path.basename(path)}: {exc}")
                continue

            self.fasta_stats.sequence_count += len(records)
            for rec in records:
                self.fasta_stats.lengths.append(rec.length)
                self.fasta_stats.gc_contents.append(rec.gc_content)
                self.fasta_stats.n_counts.append(rec.n_count)
                nid = normalize_id(rec.isolate_id)
                if nid in fasta_by_id:
                    self.fasta_stats.duplicate_ids.append(nid)
                    self.errors.append(f"Duplicate FASTA isolate ID: {rec.isolate_id}")
                else:
                    fasta_by_id[nid] = rec

        return fasta_by_id

    def _enumerate_fasta_files(self) -> List[str]:
        src = self.fasta_source
        if zipfile.is_zipfile(src):
            return self._extract_zip(src)
        if os.path.isdir(src):
            return [
                os.path.join(src, f)
                for f in sorted(os.listdir(src))
                if f.lower().endswith((".fasta", ".fa", ".fna", ".fas", ".txt"))
            ]
        self.errors.append(f"FASTA source not found or not a zip: {src}")
        return []

    def _extract_zip(self, zip_path: str) -> List[str]:
        import tempfile

        tmp = tempfile.mkdtemp(prefix="biofilm_seq_")
        extracted = []
        with zipfile.ZipFile(zip_path) as z:
            for name in z.namelist():
                if name.lower().endswith((".fasta", ".fa", ".fna", ".fas", ".txt")):
                    out = os.path.join(tmp, os.path.basename(name))
                    with z.open(name) as src, open(out, "wb") as dst:
                        dst.write(src.read())
                    extracted.append(out)
        return extracted

    # ── Step 3: isolate matching ──────────────────────────────────────────

    def _match_isolates(self, fasta_by_id: Dict[str, FastaRecord]):
        """Bidirectional matching: metadata ↔ FASTA."""
        metadata_ids = {r.metadata_fields.get("_norm_id", "") for r in self.records}
        fasta_ids = set(fasta_by_id.keys())

        unmatched_metadata = metadata_ids - fasta_ids
        unmatched_fasta = fasta_ids - metadata_ids

        if unmatched_metadata:
            self.errors.append(
                f"{len(unmatched_metadata)} metadata isolates have no FASTA file: "
                f"{sorted(unmatched_metadata)[:10]}"
            )
        if unmatched_fasta:
            self.errors.append(
                f"{len(unmatched_fasta)} FASTA files have no metadata isolate: "
                f"{sorted(unmatched_fasta)[:10]}"
            )

        for rec in self.records:
            nid = rec.metadata_fields.get("_norm_id", "")
            fasta = fasta_by_id.get(nid)
            if fasta is not None:
                rec.fasta_path = "matched"
                rec.sequence_length = fasta.length
                rec.gc_content = fasta.gc_content
                if not sequence_is_valid(fasta.sequence):
                    self.errors.append(
                        f"Isolate {rec.isolate_id}: sequence contains <80% valid "
                        "nucleotide characters"
                    )

        self.matched_count = len(metadata_ids & fasta_ids)
        self.unmatched_count = len(unmatched_metadata) + len(unmatched_fasta)

    # ── Step 4: reproducible split ────────────────────────────────────────

    def _build_split(self):
        """Isolate-level stratified train/val/test split (leakage-safe)."""
        labelled = [r for r in self.records if r.label is not None]
        if not labelled:
            self.errors.append("No labelled samples — cannot split")
            self.splits = {"train": [], "val": [], "test": []}
            return

        import sklearn.model_selection as ms

        df = pd.DataFrame(
            [{"_id": r.isolate_id, "_label": r.label} for r in labelled]
        )
        stratify = df["_label"] if df["_label"].nunique() > 1 else None

        def _try_stratified():
            train, temp = ms.train_test_split(
                df, test_size=0.3, random_state=self.seed, stratify=stratify
            )
            stratify_temp = temp["_label"] if stratify is not None else None
            val, test = ms.train_test_split(
                temp, test_size=0.5, random_state=self.seed + 1,
                stratify=stratify_temp,
            )
            return train, val, test

        def _plain():
            train, temp = ms.train_test_split(
                df, test_size=0.3, random_state=self.seed
            )
            val, test = ms.train_test_split(
                temp, test_size=0.5, random_state=self.seed + 1
            )
            return train, val, test

        try:
            train, val, test = _try_stratified()
        except ValueError:
            # e.g. a class has <2 members in a subset — fall back to plain split
            self.warnings.append(
                "Stratified split not possible (class too small in a subset); "
                "falling back to a plain isolate-level split."
            )
            train, val, test = _plain()

        self.splits = {
            "train": train["_id"].tolist(),
            "val": val["_id"].tolist(),
            "test": test["_id"].tolist(),
        }

    # ── Manifest ──────────────────────────────────────────────────────────

    def _build_manifest(self) -> ExperimentManifest:
        label_dist = {}
        missing_summary: Dict[str, Dict] = {}
        for r in self.records:
            label = r.label
            key = "pathogenic" if label == 1 else "commensal" if label == 0 else "missing"
            label_dist[key] = label_dist.get(key, 0) + 1

        if self.metadata_df is not None:
            for col in self.metadata_df.columns:
                n_missing = int(self.metadata_df[col].isna().sum())
                if n_missing > 0:
                    missing_summary[col] = {
                        "missing": n_missing,
                        "total": int(len(self.metadata_df)),
                    }

        return ExperimentManifest(
            sample_count=len(self.records),
            fasta_file_count=self.fasta_stats.file_count,
            matched_sample_count=self.matched_count,
            unmatched_sample_count=self.unmatched_count,
            metadata_columns=list(self.metadata_df.columns) if self.metadata_df is not None else [],
            label_distribution=label_dist,
            missing_value_summary=missing_summary,
            sequence_length_statistics=self.fasta_stats.length_summary,
            split_counts={k: len(v) for k, v in self.splits.items()},
        )

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _map_label(epidemiology) -> Optional[int]:
        if pd.isna(epidemiology):
            return None
        s = str(epidemiology).strip().lower()
        if s in POSITIVE_VALUES:
            return 1
        if s in NEGATIVE_VALUES:
            return 0
        return None

    def audit(self) -> Dict:
        """Human/JSON-readable audit report."""
        manifest = self.manifest
        label_dist = manifest.label_distribution if manifest else {}
        return {
            "total_samples": manifest.sample_count if manifest else 0,
            "pathogenic_count": label_dist.get("pathogenic", 0),
            "commensal_count": label_dist.get("commensal", 0),
            "class_balance_ratio": (
                round(
                    max(label_dist.get("pathogenic", 0), label_dist.get("commensal", 0))
                    / max(min(label_dist.get("pathogenic", 0), label_dist.get("commensal", 0)), 1),
                    2,
                )
                if label_dist.get("pathogenic") and label_dist.get("commensal")
                else None
            ),
            "sequence_length_statistics": (
                manifest.sequence_length_statistics if manifest else {}
            ),
            "duplicate_check": {
                "duplicate_isolate_ids_in_metadata": self._duplicate_metadata_ids(),
                "duplicate_fasta_ids": len(self.fasta_stats.duplicate_ids),
            },
            "missing_value_check": (
                manifest.missing_value_summary if manifest else {}
            ),
            "isolate_matching_check": {
                "matched": manifest.matched_sample_count if manifest else 0,
                "unmatched": manifest.unmatched_sample_count if manifest else 0,
            },
            "split_counts": manifest.split_counts if manifest else {},
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def _duplicate_metadata_ids(self) -> int:
        if self.metadata_df is None or self.id_column is None:
            return 0
        norm = self.metadata_df[self.id_column].map(
            lambda v: normalize_id(v) if pd.notna(v) else ""
        )
        return int(norm[norm.duplicated()].nunique())
