# BiofilmAI — Methodology

## 1. Data Collection Requirements

BiofilmAI is designed to accept four complementary data modalities for each sample.

| Modality | Information Captured | File Format | Preprocessing Output |
|---|---|---|---|
| Microscopy | Visual structure of microbial organization, biofilm morphology | PNG, JPG, TIFF (RGB) | Tensor (3, 224, 224) normalized |
| Spectroscopy | Chemical and molecular signatures | CSV, TXT (wavelength, intensity) | Tensor (1024, 2) z-score normalized |
| Genomics | Genomic features, pathogen-related characteristics | CSV, TXT, FASTA (nucleotide sequences) | Tensor (2048,) integer-encoded + mask |
| Clinical Data | Sample context, infection site, chronicity, treatment history | JSON or flat CSV columns | Tensor (32,) one-hot encoded |

Samples are identified by a unique `sample_id` that links all modalities.

**Current status:** No real labelled multimodal dataset is available. The system operates in DEMO MODE.

## 2. Data Validation

**File validation:** Extensions and sizes are checked against allowed lists for each modality.

**Input validation:** Sample ID, Study ID, and Sample Type are required. Chronicity must be 0–3650 days.

**PII check:** A basic heuristic scans for potential personally identifiable information in sample identifiers.

Invalid requests return structured 400 errors with `field` and `message` keys.

## 3. Preprocessing

Each modality has a dedicated pipeline in `backend/ml/preprocessing/`.

**Microscopy:** Load image → Resize to 224×224 → Normalize (ImageNet stats) → Tensor (1, 3, 224, 224)

**Spectroscopy:** Parse CSV/TXT → Extract (wavelength, intensity) → Z-score normalize → Pad/truncate to 1024 → Tensor (1, 1024, 2)

**Genomics:** Parse FASTA (skip headers) or CSV/TXT → Convert A/C/G/T to indices 0-3 → Pad/truncate to 2048 → Create attention mask → Tensor (1, 2048) + Tensor (1, 2048) mask

**Clinical:** Extract features from dict → One-hot encode categoricals → Normalize numeric (chronicity/365) → Tensor (1, 32)

## 4. Modality-Specific Encoding

Each modality is encoded by a separate neural network producing a 256-dimensional representation.

### Vision Encoder (Microscopy)
Vision Transformer (ViT): patch_size=16, embed_dim=256, num_layers=6, num_heads=8. Output is the CLS token projected to 256-dim.

### Spectral Encoder (Spectroscopy)
1D Transformer: hidden_dim=256, num_layers=4, num_heads=8. Global average pooling over the sequence.

### Genomic Encoder (Genomics)
Nucleotide embedding + Transformer: vocab=4, embed_dim=128, hidden_dim=256, num_layers=4, num_heads=8. Masked global average pooling.

### Clinical Encoder (Clinical Data)
3-layer MLP: input_dim=32, hidden_dim=256, activation=GELU, dropout=0.1.

## 5. Cross-Attention Fusion

The four modality embeddings (each 256-dim) are combined via cross-attention:

1. **Modality Projection**: `Linear(256→256)` for each modality
2. **Modality Tokens**: Learnable position embedding for each modality
3. **Cross-Attention Blocks × 4**: Each block: self-attention + cross-attention + MLP
4. **Mean Pooling**: Aggregate the four modalities
5. **Output Projection**: 256 → 128-dim unified representation

The result is a 128-dim unified multimodal representation.

## 6. Prediction Head

```
Unified (128-dim) → Linear(128, 128) → GELU → Dropout(0.1) → Linear(128, 1) → Sigmoid
```

Classified into:
- **Low**: < 0.4
- **Intermediate**: 0.4–0.7
- **High**: > 0.7

## 7. Missing-Modality Handling

- Missing modalities receive zero embeddings in the fusion layer
- A modality mask (`Dict[str, bool]`) tells the model which modalities are real
- The model produces a prediction using whatever is available

## 8. Inference

**Demo Mode (default):** Heuristic + random noise. Outputs clearly labeled as demo.
**Real Mode** (requires trained weights): Full PyTorch pipeline. Sets `demoMode=False`.

No trained weights exist currently.

## 9. Training Procedure (Future)

When a real labelled dataset is available:

1. Split: Stratified train/val/test (70/15/15)
2. Loss: Binary cross-entropy (BCE)
3. Optimizer: AdamW (lr=1e-4)
4. Early stopping: patience=10
5. Evaluation: Accuracy, Precision, Recall, F1, ROC-AUC, PR-AUC
6. Ablation study: Remove each modality to measure contribution

**No training has been performed. No fake metrics exist.**

---
*Last updated: August 2026*