# BiofilmAI — Multimodal ML Pipeline

## Model Architecture

```
Microscopy  ─→ Vision Encoder (ViT)        ─→ \
Spectroscopy ─→ Spectral Encoder (Transformer) ─→ → Cross-Attention Fusion ─→ Biofilm Risk
Genomics    ─→ Genomic Encoder (Transformer) ─→ /
Clinical    ─→ Clinical Encoder (MLP)      ─→ /
```

The model is a **multimodal transformer with cross-attention fusion**:

1. **Vision Encoder** — A Vision Transformer (ViT) that processes microscopy images (224×224 RGB) by splitting into patches, applying self-attention, and producing a fixed-size embedding.

2. **Spectral Encoder** — A 1D transformer that processes spectroscopy data (wavelength/intensity pairs). Supports sequences up to 1024 points.

3. **Genomic Encoder** — A transformer that processes nucleotide sequences (A/C/G/T) with learned embeddings. Supports sequences up to 2048 base pairs.

4. **Clinical Encoder** — An MLP that processes 32 structured clinical features (one-hot encoded categoricals + normalized numerics + bias).

5. **Cross-Attention Fusion** — A stack of cross-attention transformer blocks that learn relationships between modality embeddings. Each modality attends to every other modality. Produces a unified 128-dimensional representation.

6. **Prediction Head** — A 2-layer MLP that maps the fused representation to a biofilm probability (0–1) via sigmoid activation.

## Input Expected by Each Modality

| Modality | File Format | Expected Content | Max Size |
|---|---|---|---|
| Microscopy | PNG, JPG, TIFF | RGB microscopy image (224×224 auto-resized) | 50 MB |
| Spectroscopy | CSV, TXT | Two columns: wavelength/ wavenumber, intensity | 20 MB |
| Genomics | FASTA, CSV, TXT | Nucleotide sequences (A/C/G/T/U) | 20 MB |
| Clinical | JSON (form data) | Structured fields as defined in API | N/A |

## Preprocessing Requirements

Each modality has its own preprocessing pipeline in `backend/ml/preprocessing/`:

- **Microscopy**: Load → Resize to 224×224 → Normalize (ImageNet stats) → Tensor (1,3,224,224)
- **Spectroscopy**: Parse CSV → Z-score normalize → Pad/truncate to 1024 → Tensor (1,1024,2)
- **Genomics**: Parse FASTA/CSV → Nucleotide→Index mapping → Pad/truncate to 2048 → Tensor (1,2048) + mask
- **Clinical**: Extract features → One-hot encode → Normalize → Tensor (1,32)

## Missing-Modality Handling

The model supports missing modalities via **modality masks**:

- If a modality is not provided, a zero embedding is used in the fusion layer
- The modality mask tells the cross-attention which embeddings are real vs. padding
- The model can produce a prediction with any subset of modalities
- Contribution scores reflect the relative imortance of each available modality

## Training Workflow

Training requires a labeled dataset with the following structure:

```
dataset/
├── train/
│   ├── microscpy/       # Images
│   ├── spectroscopy/    # CSV/TXT files
│   ├── genomics/        # FASTA/CSV files  
│   ├── clinical.csv     # Clinical data (indexed by sample ID)
│   └── labels.csv       # Binary biofilm labels
├── val/
│   └── ...
└── test/
    └── ...
```

To train:

```python
from ml.training import Trainer
from ml.config import get_traning_config
from ml.model import MultimodalModel

model = MultimodalModel()
trainer = Trainer(model, get_training_config())
history = trainer.train(train_loader, val_loader)
# Weights saved to weights/model_epoch_N.pt
```

Configuration is in `backend/ml/config.py`:
- `TrainingConfig` — epochs, batch_size, learning_rate, weight_decay, etc.
- `ModelConfig` — hidden dimensions, layer counts, attention heads, etc.

## Evaluation Workflow

```python
from ml.evaluation import Evaluator

evaluator = Evaluator(model, get_evaluation_config())
metrics = evaluator.evaluate(test_loader)
# Returns: accuracy, precision, recall, f1, roc_auc, pr_auc
```

## How Trained Weights Will Be Loaded

1. Place the trained `.pt` file at `weights/biofilm_model.pt`
2. Set `BIOFILM_DEMO_MODE=false` environment variable
3. Restart the API server
4. The model manager will load the weights automatically
5. All inference calls will use the real model instead of demo mode

Alternatively:
```bash
# Custom path
export BIOFILM_WEIGHTS_PATH=/path/to/weights.pt
export BIOFILM_DEMO_MODE=false
```

The model manager in `backend/ml_manager.py` handles the lifecycle:
- Checks for weights at startup
- Loads them if available
- Falls back to demo mode if not
- Provides a unified inference interface

## Limitations

1. **No trained weights yet** — The model architecture is complete but untrained. No real labelled dataset is currently available.

2. **No clinical performance** — No accuracy, sensitivity, specificity, or AUC values exist. All current predictions are from the demo engine and are clearly labeled as such.

3. **Demo mode is the default** — The system always starts in demo mode. Only when trained weights are provided and the environment variable is set will real inference be used.

4. **Preprocessing is a placeholder** — The preprocessing pipelines are implemented but have not been validated against real data. They may need adjustment when a real dataset becomes available.

5. **Training expects a specific dataset structure** — The trainer expects a certain data loader interface. Real data integration may require adapter code.

6. **No ablation study data** — The evaluator has infrastructure for ablation studies but cannot run them without labeled data.

7. **Cross-attention → response conversion is minimal** — The real attention weights from the model are not yet fully converted into the API's CrossAttentionMap format. The demo's synthetic attention matrix is returned instead.

## Module Structure

```
backend/ml/
├── __init__.py               # Package metadata
├── README.md                 # This file
├── config.py                 # Model/training/evaluation configuration
├── model.py                  # Combined multimodal model
├── encoders/
│   ├── __init__.py
│   ├── microscopy_encoder.py # Vision Transformer
│   ├── spectroscopy_encoder.py# 1D Spectral Transformer
│   ├── genomics_encoder.py   # Genomic Transformer
│   └── clinical_encoder.py   # Clinical MLP
├── fusion/
│   ├── __init__.py
│   └── cross_attention.py   # Cross-attention fusion transformer
├── preprocessing/
│   ├── __init__.py
│   ├── microscopy.py
│   ├── spectroscopy.py
│   ├── genomics.py
│   └── clinical.py
├── training/
│   ├── __init__.py
│   └── trainer.py
├── evaluation/
│   ├── __init__.py
│   └── evaluator.py
├── inference/
│   ├── __init__.py
│   └── predictor.py          # Production inference interface
└── data/                     # Dataset management (NEW)
    ├── __init__.py
    ├── schema.py             # Dataset schema specification
    ├── dataset.py            # PyTorch Dataset
    ├── dataloader.py         # DataLoader factory
    ├── validator.py          # Dataset validation
    ├── splitter.py           # Train/val/test splitting
    └── validate_dataset.py   # CLI validation script
```

---

# Dataset Specification

## Dataset Structure Created

The following dataset infrastructure has been implemented in `backend/ml/data/`:

| File | Purpose |
|---|---|
| `schema.py` | Column/field definitions, file extension lists, expected tensor shapes |
| `dataset.py` | PyTorch `Dataset` that loads samples lazily, compatible with `MultimodalModel.forward()` |
| `dataloader.py` | `get_dataloaders()` factory returning `{"train", "val", "test", "full"}` |
| `validator.py` | `DatasetValidator` — checks structure, files, labels, duplication, leakage |
| `splitter.py` | Stratified train/val/test splitting with optional pre-assigned split column |
| `validate_dataset.py` | CLI script: `python -m backend.ml.data.validate_dataset /path/to/dataset [--json]` |

## Dataset Validation Functionality

Run the validation script to check any dataset directory:

```bash
# From the project root:
python -m backend.ml.data.validate_dataset ./dataset

# With verbose JSON output:
python -m backend.ml.data.validate_dataset ./dataset --json
```

The validator reports:

- Total samples
- Samples with microscopy
- Samples with spectroscopy
- Samples with genomics
- Samples with clinical data
- Complete multimodal samples (all 4 modalities)
- Missing modality counts
- Positive labels
- Negative labels
- Duplicate sample IDs
- Invalid files (missing, wrong extension)
- Possible data leakage
- Class imbalance ratio

If no dataset directory exists, it reports:
```
NO REAL DATASET AVAILABLE — MODEL REMAINS IN DEMO MODE.
```

## Current Status

| Asset | Status |
|---|---|
| Dataset infrastructure | ✅ Created |
| Real dataset present | ❌ No |
| Demo mode | ✅ Active |
| Trained weights | ❌ None |

## What Exact Data Is Still Required

### 1. Dataset directory

Create a directory (e.g. `/home/user/biofilm-ai/dataset/`) with this structure:

```
dataset/
├── sample_metadata.csv    # REQUIRED — master index file
├── microscopy/            # OPTIONAL — microscopy image files
├── spectroscopy/          # OPTIONAL — spectroscopy data files
├── genomics/              # OPTIONAL — genomic sequence files
└── clinical/              # OPTIONAL — clinical data JSON files
```

### 2. Metadata CSV (`sample_metadata.csv`)

| Column | Required | Type | Description |
|---|---|---|---|
| `sample_id` | Yes | string | Unique sample identifier (used as filename stem) |
| `biofilm_label` | Yes | 0 or 1 | Binary label (0 = no biofilm, 1 = biofilm detected) |
| `microscopy_path` | Optional | string | Relative path from dataset root to image file |
| `spectroscopy_path` | Optional | string | Relative path from dataset root to spectroscopy file |
| `genomics_path` | Optional | string | Relative path from dataset root to genomics file |
| `clinical_path` | Optional | string | Relative path from dataset root to clinical JSON file |
| `dataset_split` | Optional | train/val/test | Pre-assigned split. Auto-stratified if absent. |

### 3. File Formats By Modality

| Modality | Extensions | Format Notes |
|---|---|---|
| **Microscopy** | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif` | RGB images; auto-resized to 224×224 |
| **Spectroscopy** | `.csv`, `.txt` | Two columns: wavelength/ wavenumber, intensity |
| **Genomics** | `.csv`, `.txt`, `.fasta`, `.fa`, `.fna` | Nucleotide sequence (A/C/G/T/U). FASTA headers are skipped. |
| **Clinical** | `.json` or flat CSV columns | Structured fields (infection_context, chronicity_days, etc.) |

### 4. Sample ID Convention

- Must be unique across all samples
- Should be usable as a filename stem (no spaces, no special characters)
- Example: `SP-001`, `SAMPLE_42`, `patient_123`
- The `sample_id` in the CSV links the sample across all modalities

### 5. Handling of Missing Modalities

- The model supports **any subset** of modalities
- Missing modalities are indicated by leaving the corresponding path column empty (or absent)
- The model will still produce a prediction using whatever modalities are available
- The validator reports missing modality counts

### 6. Train/Val/Test Split

- 70/15/15 by default (configurable in `DatasetSpec`)
- Stratified by label (preserves class balance in each split)
- Can be pre-assigned via the `dataset_split` column
- Automatically computed if the column is absent
- Random seed = 42 (configurable)

### 7. Quality Checks

Run by the validator:
- All referenced files exist
- File extensions match the allowed list
- No duplicate sample IDs
- Labels are binary (0 or 1), not NaN
- Splits are non-overlapping
- Class imbalance < 5:1 (warning otherwise)

### 8. Data Leakage Prevention

- Duplicate sample IDs are rejected
- All samples in one split triggers a warning
- Stratification ensures class balance across splits
- The splitter uses a fixed random seed for reproducibility

### 9. Class Balance

- The validator reports positive/negative counts and an imbalance ratio
- If the ratio exceeds 5:1 a warning is raised
- Stratified splitting attempts to maintain balance across train/val/test

## Adding a Real Dataset Walkthrough

```bash
# 1. Create the dataset directory
mkdir -p /home/user/biofilm-ai/dataset/{microscopy,spectroscopy,genomics,clinical}

# 2. Place your files in the appropriate directories

# 3. Create the metadata CSV at /home/user/biofilm-ai/dataset/sample_metadata.csv
#    with columns: sample_id, biofilm_label, microscopy_path, ...

# 4. Validate the dataset
python -m backend.ml.data.validate_dataset /home/user/biofilm-ai/dataset

# 5. If validation passes, the dataset can be loaded via:
#    from backend.ml.data import BiofilmDataset, get_dataloaders

# 6. Train the model (see training workflow above)

# 7. Place trained weights at weights/biofilm_model.pt

# 8. Set BIOFILM_DEMO_MODE=false and restart the API
```

## Important Notes

- **No dataset is bundled** with this project. You must provide your own labelled data.
- **No automatic download** is performed. The system will not fetch any dataset without explicit user action.
- **No synthetic data** is generated. The validation script clearly reports when no data is available.
- **Demo mode remains active** until trained weights and labelled data are both provided.