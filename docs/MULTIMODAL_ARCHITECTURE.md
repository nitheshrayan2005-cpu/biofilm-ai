# BiofilmAI — Multimodal Research Architecture (Scaffold)

## Status

**ARCHITECTURE ONLY — NOT TRAINED.**

The multimodal model is an untrained PyTorch scaffold. It returns
`model_mode = "untrained_multimodal"`, never produces a prediction, and
`predict()` raises a clear error. No paired four-modality dataset exists
yet, so no training has been performed and no scientific performance is
claimed.

## Current Validated Experiment (separate branch)

| | |
|---|---|
| **Genomics → pathogenic vs commensal** | ✅ validated (Logistic Regression, see `evaluation_report.md`) |

The genomic Logistic Regression is a **separate validated research
baseline**. It is not part of the multimodal model and remains available
via `POST /api/research/genomic-predict`.

## Future Research Architecture

```
Microscopy   → MicroscopyEncoder   → ┐
Spectroscopy → SpectroscopyEncoder → ┤
Genomics     → GenomicsEncoder     → ┼→ CrossAttentionFusion → Multimodal
Clinical     → ClinicalEncoder     → ┘      Representation      → Prediction Head
```

## Modules (`backend/ml/models/`)

| Module | Role |
|---|---|
| `microscopy_encoder.py` | Vision encoder interface (224×224 RGB) |
| `spectroscopy_encoder.py` | 1D Transformer spectral encoder interface |
| `genomics_encoder.py` | Genomic token-Transformer encoder interface |
| `clinical_encoder.py` | Clinical MLP encoder interface (32-dim) |
| `cross_attention_fusion.py` | Cross-attention fusion (mask-aware) |
| `multimodal_model.py` | `MultimodalModel` scaffold: shape validation, modality masks, untrained state |
| `config.py` | `MultimodalConfig` — architecture hyper-parameters only |

Preprocessing interfaces remain at `backend/ml/preprocessing/`.

## Missing-Modality Behaviour

Every modality is optional. The model requires an explicit availability
dict:

```python
modalities_present = {
    "microscopy": True/False,
    "spectroscopy": True/False,
    "genomics": True/False,
    "clinical": True/False,
}
```

- Any subset may be present (e.g., genomics only, or genomics + clinical).
- **All modalities missing → clear `ValueError`** ("ALL MODALITIES MISSING").
- The fusion layer never assumes all modalities are present: absent
  modalities receive zero embeddings, are excluded from attention, and get
  **zero contribution scores**.
- Shape validation is strict: wrong dimensions, wrong dtypes, batch
  mismatches, and flag↔tensor inconsistencies all raise clear errors.

## Shape Contract

| Modality | Tensor shape | dtype |
|---|---|---|
| microscopy | `(B, 3, 224, 224)` | float |
| spectroscopy | `(B, seq_len, 2)` | float |
| genomics | `(B, seq_len)` | int (tokens) |
| genomics_mask | `(B, seq_len)` | bool |
| clinical | `(B, 32)` | float |

## Honest Behaviour Contract

- `forward()` → `model_mode = "untrained_multimodal"`, `prediction = None`
- `predict()` → raises `RuntimeError` (refuses to fabricate a prediction)
- Never claims biofilm-infection prediction
- Never claims clinical diagnosis

## Tests

`python -m backend.tests.test_multimodal_model` — 21 checks:

- all modalities present
- only genomics present
- genomics + clinical
- missing microscopy / spectroscopy / genomics / clinical
- all modalities missing → clear failure
- missing `modalities_present` arg → clear failure
- wrong clinical dims / wrong microscopy size / float genomics tokens /
  batch mismatch / flag↔tensor inconsistency → clear failures
- modality mask correctness (absent = 0 contribution)
- untrained state (`model_mode`, `prediction=None`, `predict()` refusal)

## What Is Still Required to Train the Multimodal Model

A **scientifically valid paired four-modality dataset**:

- the same biological samples each having microscopy, spectroscopy,
  genomics, AND clinical data
- a consistent binary label
- sample-level train/val/test splitting

Until such a dataset exists, the multimodal model remains an untrained
architecture scaffold, and the system stays in DEMO MODE for the
clinical-facing workflow.
