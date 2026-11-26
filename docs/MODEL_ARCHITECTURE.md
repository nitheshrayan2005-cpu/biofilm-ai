# BiofilmAI — Model Architecture

## Overview

The BiofilmAI model is a **multimodal Transformer with cross-attention fusion**. Four modality-specific encoders produce fixed-size embeddings that are combined via cross-attention into a unified representation for biofilm risk prediction.

```
Microscopy   ─→ Vision Encoder (ViT)             ─→ \
Spectroscopy ─→ Spectral Encoder (1D Transformer) ─→ → Cross-Attention Fusion ─→ Biofilm Risk
Genomics     ─→ Genomic Encoder (Transformer)     ─→ /
Clinical     ─→ Clinical Encoder (MLP)            ─→ /
```

---

## 1. Vision Encoder (Microscopy)

**File:** `backend/ml/encoders/microscopy_encoder.py`

A Vision Transformer (ViT) adapted for microscopy image encoding.

| Component | Configuration |
|---|---|
| Input shape | `(B, 3, 224, 224)` — RGB microscopy image, ImageNet-normalized |
| Patch size | 16×16 |
| Number of patches | 196 |
| Embedding dimension | 256 |
| Transformer layers | 6 |
| Attention heads | 8 |
| MLP ratio | 4.0 |
| Dropout | 0.1 |
| Output | `(B, 256)` — modality embedding |

**Architecture:**
```
Image → Conv2D Patch Embedding → [CLS] + Position Embed →
6× [LayerNorm → MultiheadAttention → Residual → MLP → Residual] →
LayerNorm → Extract CLS → Linear Projection → 256-dim embedding
```

---

## 2. Spectral Encoder (Spectroscopy)

**File:** `backend/ml/encoders/spectroscopy_encoder.py`

A 1D Transformer for processing spectral sequences (wavelength/intensity pairs).

| Component | Configuration |
|---|---|
| Input shape | `(B, 1024, 2)` — z-score normalized spectral data |
| Hidden dimension | 256 |
| Max sequence length | 1024 |
| Transformer layers | 4 |
| Attention heads | 8 |
| Dropout | 0.1 |
| Pooling | Global average over sequence |
| Output | `(B, 256)` — modality embedding |

**Architecture:**
```
Spectrum → Linear Projection → Position Embed →
4× [LayerNorm → MultiheadAttention → Residual → LayerNorm → MLP → Residual] →
LayerNorm → Global Average Pooling → Linear Projection → 256-dim embedding
```

---

## 3. Genomic Encoder (Genomics)

**File:** `backend/ml/encoders/genomics_encoder.py`

A Transformer that encodes nucleotide sequences.

| Component | Configuration |
|---|---|
| Input shape | `(B, 2048)` — integer-encoded nucleotides (0=A, 1=C, 2=G, 3=T) + mask `(B, 2048)` |
| Vocabulary | 4 (A, C, G, T) |
| Embedding dimension | 128 |
| Hidden dimension | 256 |
| Max sequence length | 2048 |
| Transformer layers | 4 |
| Attention heads | 8 |
| Dropout | 0.1 |
| Output | `(B, 256)` — modality embedding |

**Architecture:**
```
Sequence → Nucleotide Embedding(4→128) → Position Embed →
4× [LayerNorm → MultiheadAttention → Residual → LayerNorm → MLP → Residual] →
LayerNorm → Global Average Pooling (masked) → Linear Projection → 256-dim embedding
```

---

## 4. Clinical Encoder (Clinical Data)

**File:** `backend/ml/encoders/clinical_encoder.py`

A multi-layer perceptron for structured clinical data.

| Component | Configuration |
|---|---|
| Input shape | `(B, 32)` — one-hot encoded clinical features |
| Hidden dimension | 256 |
| Number of layers | 3 |
| Activation | GELU |
| Dropout | 0.1 |
| Output | `(B, 256)` — modality embedding |

**Architecture:**
```
Clinical features → Linear(32, 256) → GELU → Dropout →
Linear(256, 256) → GELU → Dropout →
Linear(256, 256) → LayerNorm → 256-dim embedding
```

---

## 5. Cross-Attention Fusion

**File:** `backend/ml/fusion/cross_attention.py`

The core of the multimodal model. Takes all four modality embeddings and learns attention relationships between them.

| Component | Configuration |
|---|---|
| Input | 4 × 256-dim modality embeddings (+ optional modality mask) |
| Projection | 4 × `Linear(256 → 256)` per modality |
| Modality tokens | Learnable `(4 × 256)` position embeddings |
| Fusion blocks | 4 × `CrossAttentionBlock` |
| Fusion hidden dimension | 256 |
| Attention heads | 8 |
| Output dimension | 128 |

Each `CrossAttentionBlock`:
```
LayerNorm → Self-Attention → Residual → LayerNorm → Cross-Attention → Residual → MLP → Residual
```

The unified representation is a 128-dim vector that aggregates all four modalities.

---

## 6. Prediction Head

**Implementation:** Inside `backend/ml/model.py`

**Architecture:**
```
Unified (128-dim) → Linear(128, 128) → GELU → Dropout(0.1) → Linear(128, 1) → Sigmoid
```

**Output:** Model-estimated biofilm probability in [0, 1], classified into:
- **Low**: < 0.4
- **Intermediate**: 0.4 – 0.7
- **High**: > 0.7

---

## 7. Input/Output Summary

| Stage | Input | Output |
|---|---|---|
| Vision Encoder | Image `(3, 224, 224)` | Embedding `(256,)` |
| Spectral Encoder | Spectra `(1024, 2)` | Embedding `(256,)` |
| Genomic Encoder | Sequence `(2048,)` + mask `(2048,)` | Embedding `(256,)` |
| Clinical Encoder | Clinical features `(32,)` | Embedding `(256,)` |
| Cross-Attention Fusion | 4 × embeddings `(256,)` | Unified `(128,)` |
| Prediction Head | Unified `(128,)` | Probability `(1,)` |

---

## 8. Missing-Modality Masks

Every modality encoder is optional. The following applies when a modality is absent:
- A zero tensor `(B, 256)` is used in place of the missing embedding
- A modality mask (boolean tensor) indicates which modalities are real
- The fusion layer uses the mask to ignore missing modalities during attention computation
- The model can produce a prediction with any subset of modalities

---

## 9. Weight Loading

```python
from backend.ml.inference import MultimodalPredictor

predictor = MultimodalPredictor()
predictor.load_model("weights/biofilm_model.pt")
result = predictor.predict(sample_info=sample_info, clinical_data=clinical_data, ...)
```

**No trained weights exist yet.** The weight path is configured in `backend/config.py` via `MODEL_WEIGHTS_PATH`.

---

*Last updated: August 2026*