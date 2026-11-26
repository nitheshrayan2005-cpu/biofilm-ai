# BiofilmAI — Dataset Pipeline

This module validates and loads a **real** labelled dataset for training the
multimodal model. It never creates synthetic data and never fabricates
missing modalities.

---

## What a Real Dataset Must Contain

### Strict per-sample directory layout

```
dataset/
├── manifest.csv                  # REQUIRED index of all samples
├── sample_<id>/
│   ├── microscopy/
│   │   └── image.png             # PNG / JPG / JPEG / TIFF (readable RGB image)
│   ├── spectroscopy/
│   │   └── spectra.csv           # CSV/TXT with numeric (wavelength, intensity) pairs
│   ├── genomics/
│   │   └── sequence.fasta        # FASTA / CSV / TXT nucleotide sequence (A/C/G/T/U)
│   ├── clinical/
│   │   └── clinical.json         # JSON matching the clinical schema below
│   └── label.txt                 # "0" or "1" (biofilm absent / present)
```

### manifest.csv

Every sample is explicitly recorded with its modality paths and label:

```csv
sample_id,microscopy_path,spectroscopy_path,genomics_path,clinical_path,label
sample_001,sample_001/microscopy/image.png,sample_001/spectroscopy/spectra.csv,sample_001/genomics/sequence.fasta,sample_001/clinical/clinical.json,1
sample_002,sample_002/microscopy/image.jpg,,sample_002/genomics/sequence.fasta,sample_002/clinical/clinical.json,0
```

Rules:
- `sample_id` is **required and unique**.
- Paths are **relative to the dataset root**.
- A modality path may be **empty** when that modality is genuinely missing.
  Missing modalities are **reported** by the validator — never filled in.
- `label` must be `0` or `1`. Samples without a label are invalid for training.

### Clinical JSON schema

```json
{
  "infectionContext": "chronic-wound",
  "chronicityDays": 21,
  "implantPresent": true,
  "sampleSite": "Lower leg",
  "previousTreatment": "antibiotics",
  "previousCulture": "positive-mixed",
  "additionalNotes": "",
  "sampleType": "Wound swab",
  "woundOrImplant": ""
}
```

Required fields: `infectionContext`, `chronicityDays`.

### Modality file requirements

| Modality | Extensions | Content requirements |
|---|---|---|
| Microscopy | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif` | Readable RGB image (opened and verified with Pillow) |
| Spectroscopy | `.csv`, `.txt` | At least one numeric (wavelength, intensity) pair per file |
| Genomics | `.csv`, `.txt`, `.fasta`, `.fa`, `.fna` | ≥80% nucleotide characters (A/C/G/T/U) after skipping FASTA headers |
| Clinical | `.json` | Object with required fields, correct types |

---

## Running the Validator

```bash
# From the project root:
python -m backend.ml.data.validate_dataset ./dataset

# JSON output:
python -m backend.ml.data.validate_dataset ./dataset --json
```

### Validation report contents

- valid samples
- invalid samples (+ per-sample error lists)
- missing modalities (by modality, by sample)
- duplicate samples
- invalid labels
- train/validation/test split counts (sample level)

If no dataset directory exists, the report states:

```
NO REAL DATASET AVAILABLE — MODEL REMAINS IN DEMO MODE.
```

---

## The 10 Validation Rules

1. Every sample has a **unique** `sample_id`.
2. Required modality files have **valid formats** (extension check).
3. Clinical data follows the **expected schema** (fields + types).
4. Spectroscopy contains **valid numeric** wavelength/intensity data.
5. Genomics is a **valid sequence** per the selected representation.
6. Microscopy files are **readable images** (verified with Pillow).
7. The biofilm **label is valid** (0 or 1).
8. **Duplicate samples** are detected.
9. **Missing modalities are reported**, never silently fabricated.
10. **Train/val/test splitting is at the SAMPLE level** (prevents leakage —
    a sample and all its modalities stay in one split).

---

## Loading a Validated Dataset

```python
from backend.ml.data import DatasetLoader, DatasetSpec

spec = DatasetSpec(dataset_root="./dataset")
loader = DatasetLoader(
    dataset_root="./dataset",
    split="train",
    spec=spec,
    data_available=True,   # only True once a real dataset exists
)

for item in loader:        # each item is a dict
    # item["microscopy"]    (3,224,224) tensor if present
    # item["spectroscopy"]  (1024,2) tensor if present
    # item["genomics"]      (2048,) long tensor if present
    # item["genomics_mask"] (2048,) bool tensor if present
    # item["clinical"]      (32,) tensor if present
    # item["modality_mask"] availability flags
    # item["label"]         float 0.0/1.0
    pass
```

---

## Current Status

| Asset | Status |
|---|---|
| Dataset pipeline (schema, alignment, checks, loader) | ✅ Complete |
| Real labelled multimodal dataset | ❌ Not available |
| Trained weights | ❌ Not available |
| Demo Mode | ✅ Active |

**No training can begin until a real validated dataset exists and the ML
dependencies (`backend/ml/requirements-ml.txt`) are installed.**
