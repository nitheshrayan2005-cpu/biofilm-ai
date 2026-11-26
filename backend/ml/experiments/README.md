# BiofilmAI — Modality-Specific Research Experiments

Clean per-modality experiment structure. Each experiment reuses the same
interface stack; none of them claim sample-level fusion with other
modalities.

## Experiment Map

| Experiment | Modality | Input | Target | Status |
|---|---|---|---|---|
| **EXPERIMENT_1_GENOMICS** | genomics | 343 k-mer/GC/N/length features | pathogenic vs commensal | ✅ VALIDATED (LR) |
| **EXPERIMENT_2_MICROSCOPY** | microscopy | raw image (future) | pending label | ⛔ NO DATA — scaffold only |
| **EXPERIMENT_3_SPECTROSCOPY** | spectroscopy | raw spectrum (future) | pending label | ⛔ NO DATA — scaffold only |
| **EXPERIMENT_4_CLINICAL_METADATA** | clinical metadata | 32-dim encoded metadata | pending label | ⛔ NO DATA — scaffold only |

## Interface Stack (shared across experiments)

| Interface | Module | Experiment 1 usage |
|---|---|---|
| Dataset registry | `backend/ml/registry.py` | `dryad_epidermidis_genomic` registered |
| Preprocessing | `backend/ml/preprocessing/` | `genomic_features.py` |
| Dataset validation | `backend/ml/data/dataset_checks.py`, `validator.py` | used in audit |
| Train/val/test split | `backend/ml/data/modality_alignment.py` (`split_samples`) | isolate-level 72/15/16 |
| Model training | `backend/ml/training/trainer.py`, `experiments/run_genomic_experiment.py` | LR/RF/MLP |
| Evaluation | `backend/ml/evaluation/evaluator.py`, `experiments/evaluate_genomic_experiment.py` | CV + test metrics |
| Artifact saving | `backend/ml/artifacts/` | weights, schema, metrics, figures |
| Inference | `backend/ml/inference/genomic_research_service.py` | `POST /api/research/genomic-predict` |

## Experiment Stubs (2–4)

Stub configs exist in `configs/` — they are marked `enabled: false` and
`data_available: false`. They will only become runnable when a real,
independently verified dataset is registered (see `backend/ml/registry.py`).

## Hard Rules

- No fabricated samples, features, or labels.
- No merging of unrelated datasets; no implied sample-level pairing.
- No modality is relabelled as another (e.g., k-mer features are never
  called "spectroscopy").
- The 4-modality Cross-Attention model remains UNTRAINED and is not
  connected to the clinical-facing Results page.
