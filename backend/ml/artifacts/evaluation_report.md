# BiofilmAI — Genomic Experiment: Evaluation Report

## Research Question

Can genomic-derived features (k-mer composition, GC fraction, N fraction, sequence length) distinguish **pathogenic** from **commensal** *Staphylococcus epidermidis* isolates, in a small research dataset?

**This is a pathogenic-vs-commensal classification experiment. It is NOT a biofilm-infection predictor and makes no clinical claim.**

## Dataset

- **103** *S. epidermidis* isolates (Dryad dataset)
- **62 pathogenic** / **41 commensal**
- Source of truth: isolate metadata (Epidemiology column)
- Only **16 test isolates** — all test metrics are high-variance at this n

## Preprocessing

- FASTA genomes → 340 k-mer frequencies (k = 1..4, ACGT alphabet), normalized per sequence
- Plus 3 aggregate features: `sequence_length`, `GC_fraction`, `N_fraction`
- Total: **343 features**
- Features standardized (StandardScaler) fit **on the training portion only**
- **Epidemiology never used as an input feature** — verified zero leakage columns

## Feature Representation

| Group | Count |
|---|---|
| k-mer (k=1) | 4 |
| k-mer (k=2) | 16 |
| k-mer (k=3) | 64 |
| k-mer (k=4) | 256 |
| sequence_length / GC_fraction / N_fraction | 3 |
| **Total** | **343** |

## Split Strategy

- **Isolate-level** split (leakage-safe, seed 42): Train 72 / Val 15 / Test 16
- No isolate appears in more than one split (verified: 0 cross-split overlap)
- Test split is **untouched** during training, model selection, and CV

## Models Evaluated

1. **Logistic Regression** (baseline) — balanced class weights
2. **Random Forest** (baseline) — 500 trees, balanced class weights
3. **MLP** (343→64→1, PyTorch) — AdamW, early stopping on validation

Selected model by validation ROC-AUC: **Logistic Regression** (val ROC 0.9259)

## Cross-Validation Method (training portion only)

Stratified **5-fold CV on the 72 training isolates** (test set never used for selection):

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.7219 ± 0.1001 | 0.7750 ± 0.0592 | 0.7722 ± 0.1957 | 0.7574 ± 0.1108 | 0.8030 ± 0.1035 |
| Random Forest | 0.6371 ± 0.0885 | 0.6671 ± 0.0540 | 0.7944 ± 0.1259 | 0.7206 ± 0.0745 | 0.6548 ± 0.1385 |

## Final Untouched Test Results (16 isolates)

| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---|---|---|---|---|
| Logistic Regression | 0.6875 | 0.7273 | 0.8000 | 0.7619 | **0.7500** |
| Random Forest | 0.6250 | 0.6429 | 0.9000 | 0.7500 | **0.8000** |
| MLP | 0.6875 | 0.6923 | 0.9000 | 0.7826 | 0.5500 |

Confusion matrix (LR, test; rows=true, cols=pred): `[[3,3],[2,8]]`

## Feature Interpretation

Top LR features (standardized coefficients) and RF importances are saved as
`logistic_coefficients.csv` and `random_forest_importance.csv`.

Top features by both methods overlap on several k-mers (e.g. `kmer_GTAC`,
`kmer_CTAG`, `kmer_CAGT`), suggesting reproducible signal.

> **Caveat:** k-mer association is **not proof of biological causation**. These are
> statistical correlates in a small, single-dataset experiment.

## Error Analysis (LR, test set — 5 errors / 16)

| Isolate | True | Predicted | P(pathogenic) | Error type |
|---|---|---|---|---|
| 599 | commensal | pathogenic | 0.858 | False positive |
| 734 | commensal | pathogenic | 0.894 | False positive |
| 780 | commensal | pathogenic | 0.640 | False positive |
| 615 | pathogenic | commensal | 0.225 | False negative |
| 634 | pathogenic | commensal | 0.429 | False negative |

- **False positives: 3** (commensal isolates confidently scored pathogenic)
- **False negatives: 2** (pathogenic isolates scored commensal)
- Full table with top contributing features: `error_analysis.csv`

## Limitations

1. **Only 103 isolates** — small dataset, limited statistical power
2. **Only 16 test isolates** — all test metrics high-variance
3. **Genomic-only experiment** — no microscopy/spectroscopy/clinical fusion
4. **Target is pathogenic vs commensal** — not biofilm infection
5. **Not clinical diagnosis** — no clinical validation, no deployment
6. **No claim of generalization beyond this dataset**
7. k-mer associations are statistical, not causal

## Artifacts

- `cross_validation_metrics.json`
- `logistic_coefficients.csv` / `random_forest_importance.csv`
- `test_predictions.csv` / `error_analysis.csv`
- `evaluation_summary.json`
- Figures: `roc_curve.png`, `confusion_matrix.png`,
  `cross_validation_performance.png`, `logistic_feature_importance.png`,
  `random_forest_importance.png`, `probability_distribution.png`

---
*Experiment run: August 2026 · seed 42 · target: pathogenic vs commensal*
