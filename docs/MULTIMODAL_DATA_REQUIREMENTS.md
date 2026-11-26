# BiofilmAI — Requirements for Legitimate 4-Modality Training

## The Core Requirement

For a scientifically valid multimodal experiment, **every biological sample**
must have:

| Modality | Requirement |
|---|---|
| **Microscopy** | a raw microscopy/confocal image file for the sample |
| **Spectroscopy** | a raw spectral measurement (wavelength/intensity) for the sample |
| **Genomics** | genome/sequence data (or validated derived features) for the sample |
| **Clinical / metadata** | structured clinical or sample metadata for the sample |
| **Common sample ID** | the SAME identifier used across all four modalities |
| **Consistent target label** | one agreed binary/multi-class label per sample |

The same biological sample must be traceable across all modalities — that
is what makes fusion legitimate. Without a common sample ID and consistent
label, modalities cannot be paired.

## Registry Template

Each dataset that may be used for a modality experiment must be registered
with these fields (see `backend/ml/registry.py`):

| Field | Meaning |
|---|---|
| `dataset_name` | unique registry name |
| `source` | repository / study / DOI |
| `license` | usage terms |
| `organism` | species |
| `sample_count` | number of samples |
| `modality` | which modality (genomics / microscopy / spectroscopy / clinical) |
| `sample_id_field` | column/field holding the sample identifier |
| `target_label` | the label column + class definition |
| `paired_modalities` | which modalities exist for the SAME samples |
| `raw_or_derived` | raw measurements vs derived features — never mislabelled |
| `download_method` | how the data were obtained (no automatic downloads) |
| `preprocessing` | pipeline applied |
| `limitations` | known gaps |

**Rule:** a dataset is registered only after independent verification.
Unverified entries are rejected by `register_dataset`.

## Current Registry

| Entry | Status |
|---|---|
| `dryad_epidermidis_genomic` | ✅ verified (103 isolates; genomics + clinical metadata; derived 343 features) |
| `EXPERIMENT_2_MICROSCOPY` | ⛔ pending verification (no data) |
| `EXPERIMENT_3_SPECTROSCOPY` | ⛔ pending verification (no data) |
| `EXPERIMENT_4_CLINICAL_METADATA` | ⛔ pending verification (no data) |

## What Would Be Required to Enable Real 4-Modality Training

1. A dataset where **the same samples** have all four modalities.
2. A **common sample ID** linking every modality file to the sample.
3. A **consistent target label** for all samples.
4. Sample-level train/val/test splitting (no leakage).
5. Modality-appropriate preprocessing for each modality.
6. Independent verification + registry entry.
7. Training each encoder and the fusion model with an honest evaluation.

Until items 1–6 are satisfied, the multimodal model remains an **untrained
architecture scaffold** and the clinical-facing system stays in DEMO MODE.
