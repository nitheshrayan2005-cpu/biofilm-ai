# BiofilmAI — Dataset Schema Mapping

## How a Real Dataset Maps to BiofilmDataset

This document shows how a future real dataset maps to the existing `BiofilmDataset` loader. All paths are relative to the dataset root.

---

## Directory Structure

```
dataset/
├── sample_metadata.csv         # Master index (REQUIRED)
├── microscopy/                 # OPTIONAL — microscopy images
│   ├── SP-001.png
│   ├── SP-002.jpg
│   └── ...
├── spectroscopy/               # OPTIONAL — spectroscopy files
│   ├── SP-001.csv
│   ├── SP-002.csv
│   └── ...
├── genomics/                   # OPTIONAL — genomic sequences
│   ├── SP-001.fasta
│   ├── SP-002.fna
│   └── ...
└── clinical/                   # OPTIONAL — clinical JSON
    ├── SP-001.json
    ├── SP-002.json
    └── ...
```

---

## sample_metadata.csv Columns

| CSV Column | Maps To | Required | Example |
|---|---|---|---|
| `sample_id` | `SAMPLE_ID_COL` | Yes | `SP-001` |
| `biofilm_label` | `LABEL_COL` | Yes | `1` (biofilm) or `0` (no biofilm) |
| `microscopy_path` | `MICROSCOPY_PATH_COL` | No | `microscopy/SP-001.png` |
| `spectroscopy_path` | `SPECTROSCOPY_PATH_COL` | No | `spectroscopy/SP-001.csv` |
| `genomics_path` | `GENOMICS_PATH_COL` | No | `genomics/SP-001.fasta` |
| `clinical_path` | `CLINICAL_PATH_COL` | No | `clinical/SP-001.json` |
| `dataset_split` | `SPLIT_COL` | No | `train` / `val` / `test` |

### How the Loader Uses Each Column

1. **sample_id**: Primary key. Used for diagnostic logging and sample tracking.

2. **biofilm_label**: Read and returned as `labels` tensor with shape `(1,)`. If absent, the sample is treated as unlabelled (inference only).

3. **microscopy_path**: Relative path from dataset root. The file is read as bytes, passed through `preprocessing/microscopy.py`, and returned as `microscopy` tensor `(3, 224, 224)`. If absent, the modality is skipped (zero embedding in the fusion layer).

4. **spectroscopy_path**: Same pattern — read as bytes → preprocess → return. The `spectroscopy` tensor has shape `(1024, 2)`.

5. **genomics_path**: Same pattern. Returns `genomics` tensor `(2048,)` and `genomics_mask` tensor `(2048,)`.

6. **clinical_path**: JSON file loaded as dict, passed through `preprocessing/clinical.py`. Returns `clinical` tensor `(32,)`. Alternatively, if flat clinical columns exist in the CSV, those are used instead.

7. **dataset_split**: If present, the `DatasetSplitter` uses it as-is. If absent, the splitter creates new stratified splits.

---

## Modality -> Tensor Shape Mapping

| Modality | Dataset Field | Tensor Shape | Dtype | How Missing Modality Is Handled |
|---|---|---|---|---|
| Microscopy | `microscopy` | `(3, 224, 224)` | float32 | Zero tensor + `modality_mask["microscopy"]=False` |
| Spectroscopy | `spectroscopy` | `(1024, 2)` | float32 | Zero tensor + `modality_mask["spectroscopy"]=False` |
| Genomics | `genomics` | `(2048,)` | long | Zero tensor + `modality_mask["genomics"]=False` |
| Genomics mask | `genomics_mask` | `(2048,)` | bool | All False |
| Clinical | `clinical` | `(32,)` | float32 | Zero tensor + `modality_mask["clinical"]=False` |
| Labels | `labels` | `(1,)` | float32 | `[-1.0]` sentinel value |

---

## Validation Script

```bash
# Validate a dataset directory
python -m backend.ml.data.validate_dataset /path/to/dataset

# JSON output
python -m backend.ml.data.validate_dataset /path/to/dataset --json
```

The validator checks:
- Metadata CSV exists and has required columns
- Sample IDs are unique
- Labels are 0 or 1
- Referenced files exist and have correct extensions
- Split column (if present) has train/val/test
- Class imbalance ratio
- Data leakage risks

---

## Loading the Dataset

```python
from backend.ml.data import BiofilmDataset, get_dataloaders
from backend.ml.data.schema import DatasetSpec

# Option 1: Get DataLoaders directly
spec = DatasetSpec(dataset_root="/path/to/dataset")
loaders = get_dataloaders(
    dataset_root="/path/to/dataset",
    batch_size=32,
    data_available=True,  # Set to True when real data exists
)
train_loader = loaders["train"]
val_loader = loaders["val"]
test_loader = loaders["test"]

# Option 2: Create a Dataset directly
dataset = BiofilmDataset(
    spec=spec,
    split="train",
    data_available=True,
)

for batch in dataset:
    # batch is a dict with keys:
    #   "microscopy": (3,224,224) tensor (optional)
    #   "spectroscopy": (1024,2) tensor (optional)
    #   "genomics": (2048,) tensor (optional)
    #   "genomics_mask": (2048,) tensor (optional)
    #   "clinical": (32,) tensor (optional)
    #   "modality_mask": dict[str, bool]
    #   "labels": (1,) tensor (None if unlabelled)
    #   "sample_id": str
    pass
```

---

## Compatibility with MultimodalModel

The batch dict from `_collate_multimodal` is compatible with `MultimodalModel.forward()` arguments:

```python
model = MultimodalModel()
output = model(
    microscopy=batch["microscopy"],       # (B, 3, 224, 224) or None
    spectroscopy=batch["spectroscopy"],   # (B, 1024, 2) or None
    genomics=batch["genomics"],           # (B, 2048) or None
    clinical=batch["clinical"],           # (B, 32) or None
    modality_mask=batch["modality_mask"],  # Dict[str, (B,) bool
)
# output is a dict with:
#   "prediction": (B, 1) tensor
#   "risk_category": str
#   "modality_contributions": Dict[str, float]
```

---

## Training Cod

```python
from akend.ml.traing import Traier
from ackend.ml.confg import get_training_config

trainer = Tainer(
    odel=odal,
    onfig=get_training_config(),
    device="cpu",
)

# Creates DataLoaders internally if not provided:
history = trainer.train(
    train_loader=train_loader,
    val_loader=val_loader,
)
```

---

## How to Add Real Data When Available

1. Place files in the structure shown above
2. Create `sample_metadata.csv` 
3. Run the validator to check structure
4. Set the `dataset_root` in `ModelConfig`
5. Set `data_available=True` in `get_dataloaders()`
6. Train the model (generates weights at `weights/biofil_model.pt`)
7. Set `BIOFIL_DEMO_MODE=false` and restart the API
8. The model manager loads weights and real inference begins

**No code changes are required.** The entire pipeline from Dataset → Model → API → Frontend is designed to work without modification once real data and trained weights are provided.