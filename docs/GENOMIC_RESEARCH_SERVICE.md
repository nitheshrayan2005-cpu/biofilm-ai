# BiofilmAI — Research Genomic Inference Service

## Endpoint

```
POST /api/research/genomic-predict
```

**This is a backend-only research endpoint. It is NOT connected to the
clinical-facing Results page and is not part of the demo workflow.**

## What the Model Predicts

- **Target:** `Epidemiology` — **pathogenic vs commensal** status of
  *Staphylococcus epidermidis* isolates
- **Input:** 343 genomic-derived features:
  - 340 k-mer frequencies (k = 1–4, ACGT alphabet)
  - `sequence_length`, `GC_fraction`, `N_fraction`
- **Model:** Logistic Regression (balanced class weights), standardized
  with a scaler fit **on the training portion only**
- **Output:** predicted class + probability for each class

## What It Does NOT Predict

- ❌ Biofilm-associated infection risk
- ❌ Any clinical diagnosis
- ❌ Infection diagnosis
- ❌ Treatment decisions
- ❌ Generalization beyond this specific dataset

Every response includes:

> "Research model output: genomic classification of pathogenic vs commensal
> status. This is not a biofilm diagnosis, infection diagnosis, or clinical
> decision. Laboratory confirmation and professional judgment remain necessary."

## Dataset

| Item | Value |
|---|---|
| Isolates | 103 (62 pathogenic / 41 commensal) |
| Source | Dryad S. epidermidis dataset |
| Features | 343 genomic-derived |
| Test set | 16 isolates (untouched) |

## Evaluation Protocol (leakage-safe)

- Isolate-level split: Train 72 / Val 15 / Test 16 (seed 42), 0 cross-split overlap
- Scaler fit on train only; test set used only for final evaluation
- 5-fold stratified CV on the training portion: LR ROC-AUC 0.803 ± 0.104
- Untouched test set: LR ROC-AUC 0.75

## Validation Rules (strict)

The endpoint rejects invalid requests with HTTP 400:

| Condition | Behavior |
|---|---|
| Missing feature(s) | Rejected — names the missing features |
| Extra/unknown feature(s) | Rejected — never silently reordered or guessed |
| Non-numeric value | Rejected |
| NaN / infinity | Rejected |
| Wrong feature count | Rejected |
| Model artifact unavailable | HTTP 503 (clinical system stays in DEMO MODE) |

## Current Limitations

1. Only 103 isolates (16 in the untouched test set) — small n, high variance
2. Genomic-only — no microscopy / spectroscopy / clinical fusion
3. Target is pathogenic-vs-commensal, **not** biofilm infection
4. k-mer associations are statistical, not causal
5. Not clinically validated; not a medical device
6. No claim of generalization beyond this dataset

## Why It Is Not a Clinical Diagnostic Model

- It was trained on a single small research dataset with a coarse
  phenotype label (pathogenic vs commensal) derived from isolation source
- It has not been validated on independent cohorts or patient outcomes
- It has not undergone regulatory review (FDA / CE / CDSCO)
- Its purpose is research and methodology demonstration only

## Files

- Service: `backend/ml/inference/genomic_research_service.py`
- Model artifact: `backend/ml/artifacts/logistic_regression_model.json`
- Feature schema: `backend/ml/artifacts/feature_schema.json`
- Tests: `backend/tests/test_genomic_predict.py` (16 checks)
- Evaluation report: `backend/ml/artifacts/evaluation_report.md`

## Test

```bash
python -m backend.tests.test_genomic_predict
```
