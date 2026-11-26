"""
BiofilmAI Data — FASTA Parser
===============================

Parses FASTA genome files and computes sequence statistics.

Used by the genomic experiment loader for:
  - reading isolate genome sequences
  - validating FASTA structure
  - computing sequence statistics (length, GC content, N content)

This module contains NO biological data — it only parses files that the
user provides.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# FASTA header → isolate ID: take the first whitespace-delimited token,
# strip '>', and remove common accession prefixes.
HEADER_ID_PATTERN = re.compile(r"^[>\s]*([^\s|]+)")
VALID_BASES = set("ACGTU")
AMBIGUITY_CODES = set("RYSWKMBDHVN")


@dataclass
class FastaRecord:
    """A single parsed FASTA entry."""
    header: str
    isolate_id: str
    sequence: str
    length: int
    gc_content: float
    n_count: int
    ambiguity_count: int


@dataclass
class FastaStats:
    """Aggregate statistics over all parsed FASTA files."""
    file_count: int = 0
    sequence_count: int = 0
    lengths: List[int] = field(default_factory=list)
    gc_contents: List[float] = field(default_factory=list)
    n_counts: List[int] = field(default_factory=list)
    duplicate_ids: List[str] = field(default_factory=list)
    invalid_files: List[str] = field(default_factory=list)

    @property
    def length_summary(self) -> Dict:
        if not self.lengths:
            return {"min": 0, "max": 0, "mean": 0.0, "median": 0.0, "total_bp": 0}
        import statistics
        return {
            "min": min(self.lengths),
            "max": max(self.lengths),
            "mean": round(statistics.mean(self.lengths), 1),
            "median": float(statistics.median(self.lengths)),
            "total_bp": sum(self.lengths),
        }

    @property
    def gc_summary(self) -> Dict:
        if not self.gc_contents:
            return {"min": 0.0, "max": 0.0, "mean": 0.0}
        import statistics
        return {
            "min": round(min(self.gc_contents), 4),
            "max": round(max(self.gc_contents), 4),
            "mean": round(statistics.mean(self.gc_contents), 4),
        }


def parse_fasta_file(path: str) -> List[FastaRecord]:
    """
    Parse a FASTA file into FastaRecord objects.

    Raises ValueError if the file is empty or contains no valid records.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"FASTA file not found: {path}")

    records: List[FastaRecord] = []
    header: Optional[str] = None
    lines: List[str] = []

    def flush():
        nonlocal header, lines
        if header is not None:
            seq = "".join(lines).replace(" ", "").upper()
            records.append(_build_record(header, seq))
        header = None
        lines = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                flush()
                header = line
            else:
                if header is None:
                    raise ValueError(
                        f"Sequence line before any header in {path}"
                    )
                lines.append(line)
    flush()

    if not records:
        raise ValueError(f"No FASTA records found in {path}")
    return records


def _build_record(header: str, sequence: str) -> FastaRecord:
    if not sequence:
        raise ValueError(f"Empty sequence for header '{header}'")
    isolate_id = header_id(header)
    gc = 0.0
    n_count = 0
    ambiguity = 0
    for base in sequence:
        if base in ("G", "C"):
            gc += 1
        elif base == "N":
            n_count += 1
        elif base in AMBIGUITY_CODES:
            ambiguity += 1
    length = len(sequence)
    gc_content = gc / length if length else 0.0
    return FastaRecord(
        header=header,
        isolate_id=isolate_id,
        sequence=sequence,
        length=length,
        gc_content=gc_content,
        n_count=n_count,
        ambiguity_count=ambiguity,
    )


def header_id(header: str) -> str:
    """Extract a normalized isolate ID from a FASTA header."""
    match = HEADER_ID_PATTERN.match(header)
    raw = match.group(1) if match else header.lstrip(">").strip()
    return normalize_id(raw)


def normalize_id(value: str) -> str:
    """
    Normalize an isolate identifier for matching.

    Removes whitespace, lowercases, and strips common prefix artifacts so
    that e.g. 'S123', 's123', '>S123' all match.
    """
    s = str(value).strip().lower()
    for prefix in ("lcl|", "gnl|", "ref|", "gb|", "emb|", "dbj|"):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s


def sequence_is_valid(sequence: str) -> bool:
    """A sequence is valid if ≥80% of characters are IUPAC nucleotide codes."""
    if not sequence:
        return False
    valid = VALID_BASES | AMBIGUITY_CODES
    return sum(1 for c in sequence if c in valid) / len(sequence) >= 0.8
