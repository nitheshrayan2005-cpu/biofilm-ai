# BiofilmAI — Future Work

This document outlines the research pathway for taking BiofilmAI from its current prototype state to a trained, evaluated research model.

---

## 1. Acquire or Collect Paired Multimodal Samples

The most critical requirement is a dataset where each sample has all four modalities.

**Option A: Laboratory collection (recommended for academic project)**
- Collect 50–100 clinical wound swabs or in vitro biofilm samples
- For each sample: microscopy image, spectroscopy measurement, 16S sequencing, clinical metadata
- Establish consistent biofilm label (e.g., via CLSM confirmation or culture)

**Option B: Institutional collaboration**
- Partner with a hospital or research lab that has access to biofilm samples
- Share the dataset specification (see `backend/ml/data/schema.py`)

**Option C: Literature data request**
- Several published studies have collected multimodal biofilm data
- Authors may share data upon reasonable request

## 2. Establish Labeling Protocol

Define a reproducible binary biofilm label. Possible approaches:
- Confocal laser scanning microscopy (CLSM) confirmation by an expert
- Molecular markers (e.g., 16S rRNA quantification, qPCR for biofilm-associated genes)
- Culture-based methods (CFU counts with biofilm-specific staining)
- Consensus of multiple methods

The labeling method must be consistent across all samples.

## 3. Preprocess Data

Run all samples through the existing preprocessing pipelines:
- `preprocessing/microscopy.py` — resize, normalize, tensor
- `preprocessing/spectroscopy.py` — parse, normalize, pad
- `preprocessing/genomics.py` — sequence parsing, indexing, masking
- `preprocessing/clinical.py` — feature extraction, encoding

Use the `validate_dataset.py` script to verify the dataset structure.

## 4. Train Individual Encoders (Optional)

If large single-modality datasets are available, pretrain the encoders:
- **Vision Encoder**: Pretrain on DeepBacs or similar bacterial microscopy datasets
- **Spectral Encoder**: Pretrain on Ho et al. Raman bacterial spectra
- **Genomic Encoder**: Pretrain on NCBI 16S rRNA sequences

This step improves representation quality before multimodal training.

## 5. Train the Multimodal Model

Train the complete model end-to-end on the paired dataset:

```python
from backend.ml.training import Trainer
from backend.ml.config import get_training_config
from backend.ml.data import get_dataloaders

loaders = get_dataloaders(dataset_root="./dataset", data_available=True)
trainer = Trainer(model, get_training_config())
history = trainer.train(loaders["train"], loaders["val"])
```

Training configuration (defaults):
- Epochs: 100 (with early stopping at patience=10)
- Batch size: 32
- Optimizer: AdamW (lr=1e-4, weight_decay=1e-5)
- Loss: Binary cross-entropy
- Scheduler: Cosine annealing with 100-step warmup

## 6. Evaluate Using Proper Train/Validation/Test Separation

Use the existing `Evaluator` class:

```python
from backend.ml.evaluation import Evaluator

evaluator = Evaluator(model)
metrics = evaluator.evaluate(loaders["test"])
```

Report:
- Accuracy
- Precision
- Recall
- F1-score
- ROC-AUC
- PR-AUC

All metrics must be computed on a held-out test set that was never used during training or validation.

## 7. Perform Ablation Studies

Evaluate the contribution of each modality by removing it:

| Model Variant | Modalities Used |
|---|---|
| Full model | All 4 |
| Without microscopy | Spectroscopy + Genomics + Clinical |
| Without spectroscopy | Microscopy + Genomics + Clinical |
| Without genomics | Microscopy + Spectroscopy + Clinical |
| Without clinical | Microscopy + Spectroscopy + Genomics |
| Without cross-attention | Concatenation baseline |

This reveals which modalities are most informative for the prediction task.

## 8. Evaluate Missing-Modality Robustness

Test the model when one or more modalities are missing at inference time. This is critical for real-world application where data may be incomplete.

## 9. Investigate Explainability

Enhance the interpretation module:
- Convert real cross-attention weights into the API's CrossAttentionMap format
- Generate Grad-CAM heatmaps for microscopy attention
- Identify which spectral regions drive predictions
- Link genomic attention to specific gene regions

## 10. Validate on Independent Data

Test the trained model on data from a different source, laboratory, or patient population. This is essential to understand generalization.

## 11. Deploy with Real Inference

Once trained and validated:

```bash
export BIOFILM_DEMO_MODE=false
export BIOFILM_WEIGHTS_PATH=/path/to/trained_model.pt
```

Restart the API server. The ModelManager will detect the weights, load the model, and all `/api/analyze` requests will use the real model. No frontend changes are required.

---

## Summary of Future Work

| Step | Effort | Priority |
|---|---|---|
| Acquire multimodal dataset | High | Critical |
| Establish labeling protocol | Medium | Critical |
| Preprocess and validate data | Medium | High |
| Train encoders (optional) | Low-Medium | Medium |
| Train fusion model | Medium-High | High |
| Evaluate and ablate | Medium | High |
| Explainability | Low-Medium | Medium |
| Independent validation | Medium | High |
| Deploy real inference | Low | After validation |

---

*Last updated: August 2026*