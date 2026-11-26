# BiofilmAI — Modality-Specific Experiment Plan

## Current Genomics Dataset (verified)

- **103** *S. epidermidis* isolates (Dryad)
- **62 pathogenic / 41 commensal** (target: `Epidemiology`)
- Input: **343 genomic-derived features** (340 k-mer + `sequence_length` + `GC_fraction` + `N_fraction`)
- Isolate-level split 72/15/16 (seed 42, leakage-safe)
- **EXPERIMENT_1_GENOMICS: VALIDATED** — Logistic Regression (5-fold CV ROC-AUC 0.803 ± 0.104; test ROC-AUC 0.75)

## What Microscopy Data Are Missing

- **No raw microscopy / confocal images exist anywhere in the project.**
- The only `.png` files are evaluation figures (ROC, confusion matrices) generated from model predictions — these are derived outputs, **not** raw microscopy.
- A real microscopy experiment requires, per sample: a raw image file (PNG/JPG/TIFF), a consistent sample ID, and a verified label.

## What Spectroscopy Data Are Missing

- **No spectral measurement files exist anywhere in the project.**
- The 340 k-mer features are **genomic-derived composition features** — they are **not** spectroscopy and must never be described as such.
- A real spectroscopy experiment requires, per sample: a raw spectral measurement (wavelength/intensity), a consistent sample ID, and a verified label.

## Clinical Metadata Currently Available

- The Dryad metadata CSV has **103 rows**, `Identifier` column, **103/103 exact match** with the genomes.
- Columns are **categorical/identifier fields**: strain, country, year, sequence type, S. epidermidis group, `Epidemiology` (target), isolation source.
- This metadata is real and genuinely sample-paired with the genomes. It is **not** a set of quantitative clinical measurements (no vitals, labs, etc.).
- It can legitimately feed the future **Clinical Encoder** (32-dim encoded vector) — but this is a future multimodal integration, not an independent validated experiment yet.

## Why Unrelated Datasets Must Not Be Fused

- Different datasets have different samples, organisms, instruments, and labelling schemes.
- There is no sample-level correspondence across independent studies.
- Fusing them and claiming multimodal prediction would be scientifically invalid — it would not be real fusion, it would be fabricated pairing.
- The multimodal Cross-Attention architecture requires **the same biological sample** traceable across all modalities.

## How Future Modality-Specific Experiments Will Be Evaluated

For each experiment (2–4), the same honest protocol applies once real data exist:

1. **Registry** — dataset must be independently verified and registered (`backend/ml/registry.py`).
2. **Preprocessing** — modality-specific pipeline (`backend/ml/preprocessing/`).
3. **Validation** — structure/label checks (`backend/ml/data/`).
4. **Split** — sample-level stratified train/val/test (never merge samples across sources).
5. **Train** — baselines (LR, RF) + the modality encoder; model selection on validation only.
6. **Evaluate** — accuracy/precision/recall/F1/ROC-AUC + confusion matrix on the untouched test set.
7. **Artifacts** — weights, feature schema, metrics, figures saved to `backend/ml/artifacts/`.
8. **Report** — honest metrics only; no fabricated performance.

## How These Could Later Feed Cross-Attention Fusion

- Each validated modality encoder produces a **fixed-dim embedding** for a sample.
- If — and only if — the same samples have real data in ≥2 modalities (common sample ID + consistent label), those per-modality embeddings can be fused by the existing **Cross-Attention Fusion** module.
- Until such paired data exist, the 4-modality model remains **untrained** and is not connected to any prediction output.
- The scaffold already supports explicit modality masks, so partial-modality samples are handled without fabrication.

## Status Summary

| Experiment | Modality | Status |
|---|---|---|
| 1 — Genomics | genomics | ✅ VALIDATED |
| 2 — Microscopy | microscopy | ⛔ NO DATA (scaffold only) |
| 3 — Spectroscopy | spectroscopy | ⛔ NO DATA (scaffold only) |
| 4 — Clinical/Metadata | clinical metadata | ⛔ NO DATA (scaffold only) |
| 4-modality fusion | all | ⛔ UNTRAINED architecture |
