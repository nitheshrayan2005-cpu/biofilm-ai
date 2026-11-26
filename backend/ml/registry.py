"""
BiofilmAI — Dataset Registry
==============================

A registry of datasets that have been independently VERIFIED for use in
modality-specific research experiments.

Rules:
  - Only verified, real datasets may be registered.
  - A dataset entry must state its source, license, sample count,
    modality, pairing, and whether data are raw or derived.
  - Unverified or fabricated datasets are REJECTED by `register_dataset`.
  - No external dataset is downloaded automatically.

Currently registered (VERIFIED):
  - dryad_epidermidis_genomic  — the real 103-isolate S. epidermidis study
                                 (metadata + genome-derived 343 features)

Experiments 2–4 (microscopy / spectroscopy / clinical-metadata) have NO
registered datasets yet: raw microscopy and spectroscopy files are not
present in the project, and no external dataset has been independently
verified. Their registry slots exist as templates only.
"""

from __future__ import annotations

from typing import Dict, List

# Required registry fields
REQUIRED_FIELDS = [
    "dataset_name",
    "source",
    "license",
    "organism",
    "sample_count",
    "modality",          # e.g. "genomics", "microscopy", "spectroscopy", "clinical"
    "sample_id_field",
    "target_label",
    "paired_modalities", # list of modalities present for the SAME samples
    "raw_or_derived",
    "download_method",
    "preprocessing",
    "limitations",
]

# ── The one VERIFIED real dataset ──────────────────────────────────────────

DRYAD_EPIDERMIDIS_GENOMIC: Dict = {
    "dataset_name": "dryad_epidermidis_genomic",
    "source": "Dryad — S. epidermidis multilocus/whole-genome study (metadata + genome files)",
    "license": "Dryad repository terms (research use; verify current terms before redistribution)",
    "organism": "Staphylococcus epidermidis",
    "sample_count": 103,
    "modality": "genomics (+ clinical/sample metadata)",
    "sample_id_field": "Identifier",
    "target_label": "Epidemiology (pathogenic=1, commensal=0)",
    "paired_modalities": ["genomics", "clinical_metadata"],
    "raw_or_derived": "derived — 343 features (340 k-mer + sequence_length + GC_fraction + N_fraction) computed from raw FASTA genomes",
    "download_method": "user-uploaded files (BiofilmAI_genomic_features.csv, Dryad_data_metadata (1).csv); no automatic download",
    "preprocessing": "FASTA → k-mer composition (k=1..4) + length + GC + N; StandardScaler fit on training split only",
    "limitations": (
        "103 isolates total; 16-isolate test set (small, high variance); "
        "genomic-only for the validated experiment; no raw microscopy or "
        "spectroscopy present; not sample-paired to any external dataset."
    ),
    "verified": True,
    "experiments": ["EXPERIMENT_1_GENOMICS"],
}

# Template for FUTURE modality-specific datasets (Experiments 2–4).
# Do NOT populate unless the dataset is independently verified.
DATASET_REGISTRY_TEMPLATE: Dict = {
    "dataset_name": "",
    "source": "",
    "license": "",
    "organism": "",
    "sample_count": 0,
    "modality": "",               # microscopy | spectroscopy | clinical
    "sample_id_field": "",
    "target_label": "",
    "paired_modalities": [],      # which modalities are present for the SAME samples
    "raw_or_derived": "",         # raw measurements OR derived features — never mislabelled
    "download_method": "",
    "preprocessing": "",
    "limitations": "",
    "verified": False,
    "experiments": [],
}

# Reserved (UNVERIFIED / EMPTY) slots — experiments 2–4 have no data yet.
EMPTY_EXPERIMENT_SLOTS: Dict[str, Dict] = {
    "EXPERIMENT_2_MICROSCOPY": dict(DATASET_REGISTRY_TEMPLATE, modality="microscopy",
                                    dataset_name="PENDING_VERIFICATION"),
    "EXPERIMENT_3_SPECTROSCOPY": dict(DATASET_REGISTRY_TEMPLATE, modality="spectroscopy",
                                      dataset_name="PENDING_VERIFICATION"),
    "EXPERIMENT_4_CLINICAL_METADATA": dict(DATASET_REGISTRY_TEMPLATE, modality="clinical",
                                           dataset_name="PENDING_VERIFICATION"),
}

DATASET_REGISTRY: Dict[str, Dict] = {
    DRYAD_EPIDERMIDIS_GENOMIC["dataset_name"]: DRYAD_EPIDERMIDIS_GENOMIC,
}


def register_dataset(entry: Dict) -> None:
    """
    Register a dataset entry ONLY if it passes validation.

    Rejects entries with missing required fields, unverified provenance,
    or a non-positive sample count. Never auto-populates from external
    sources.
    """
    errors = validate_entry(entry)
    if errors:
        raise ValueError(f"Dataset rejected — {errors}")
    DATASET_REGISTRY[entry["dataset_name"]] = entry


def validate_entry(entry: Dict) -> List[str]:
    """Return a list of validation errors (empty = valid)."""
    errors = []
    for field in REQUIRED_FIELDS:
        if field not in entry:
            errors.append(f"missing field '{field}'")
    if entry.get("verified") is not True:
        errors.append("not marked as independently verified")
    if not isinstance(entry.get("sample_count"), int) or entry.get("sample_count", 0) <= 0:
        errors.append("sample_count must be a positive integer")
    if not entry.get("dataset_name"):
        errors.append("dataset_name is required")
    return errors


def registry_status() -> Dict:
    """Summary of the registry for reporting."""
    return {
        "registered": list(DATASET_REGISTRY.keys()),
        "unverified_slots": list(EMPTY_EXPERIMENT_SLOTS.keys()),
        "note": "Only dryad_epidermidis_genomic is verified. "
                "Microscopy and spectroscopy slots are EMPTY — no fabricated data.",
    }
