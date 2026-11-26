"""
BiofilmAI — First Real Genomic Training Experiment
=====================================================

TARGET:    Epidemiology = pathogenic (1) vs commensal (0)
INPUTS:    343 genomic-derived features (340 k-mer + sequence_length +
           GC_fraction + N_fraction). Epidemiology is NEVER an input.

Protocol (leakage-safe):
    - Fixed isolate-level split (72/15/16, seed 42) already generated
      in dataset/audit/splits.json
    - train  → optimization
    - val    → model selection / early stopping
    - test   → touched ONLY for final evaluation

Models:
    1. Logistic Regression (baseline)
    2. Random Forest       (baseline)
    3. PyTorch MLP         (GenomicClassifierNet, 343 → 64 → 1)

All random seeds fixed. All artifacts saved to backend/ml/artifacts/.
"""

from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Fixed seeds for reproducibility
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

FEATURES_CSV = "/home/user/uploads/BiofilmAI_genomic_features.csv"
SPLITS_JSON = "/home/user/biofilm-ai/dataset/audit/splits.json"
ARTIFACT_DIR = Path("/home/user/biofilm-ai/backend/ml/artifacts")

# Columns that are NOT model inputs
ID_COLS = ["Identifier", "genome_file"]
TARGET_COL = "Epidemiology"

# Non-kmer feature columns (order matters for the feature schema)
NON_KMER_FEATURES = ["sequence_length", "GC_fraction", "N_fraction"]


def load_data():
    """Load features + splits; return X, y, split index dict."""
    df = pd.read_csv(FEATURES_CSV)
    with open(SPLITS_JSON) as f:
        splits = json.load(f)

    # Build feature list: all kmer_* columns (sorted deterministically),
    # then the 3 non-kmer features. 340 + 3 = 343.
    kmer_cols = sorted([c for c in df.columns if c.startswith("kmer_")])
    feature_cols = kmer_cols + NON_KMER_FEATURES
    assert len(feature_cols) == 343, f"Expected 343 features, got {len(feature_cols)}"

    # Verify no leakage columns are in the feature set
    assert TARGET_COL not in feature_cols
    assert not any(c in feature_cols for c in ID_COLS)

    X = df[feature_cols].to_numpy(dtype=np.float32)
    y = (df[TARGET_COL].astype(str).str.strip().str.lower() == "pathogenic").astype(int).to_numpy()

    id_map = {str(i): idx for idx, i in enumerate(df["Identifier"].astype(str))}
    split_idx = {
        name: [id_map[i] for i in ids if i in id_map]
        for name, ids in splits.items()
    }
    return df, feature_cols, X, y, split_idx


def metrics_report(y_true, y_pred, y_proba, name):
    """Compute standard binary classification metrics."""
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        roc_auc_score, confusion_matrix, classification_report,
    )
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    roc = roc_auc_score(y_true, y_proba) if len(set(y_true)) > 1 else float("nan")
    cm = confusion_matrix(y_true, y_pred).tolist()
    return {
        "model": name,
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1": round(f1, 4),
        "roc_auc": round(roc, 4) if not np.isnan(roc) else None,
        "confusion_matrix": cm,   # [[TN, FP], [FN, TP]]
        "classification_report": classification_report(y_true, y_pred, output_dict=True, zero_division=0),
    }


def main():
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    df, feature_cols, X, y, split_idx = load_data()

    train_idx = split_idx["train"]
    val_idx = split_idx["val"]
    test_idx = split_idx["test"]

    # Standardize features — fit scaler on TRAIN ONLY (prevents leakage)
    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler().fit(X[train_idx])
    X = scaler.transform(X)

    X_train, y_train = X[train_idx], y[train_idx]
    X_val, y_val = X[val_idx], y[val_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    print("=" * 70)
    print("BiofilmAI — First Real Genomic Training Experiment")
    print("=" * 70)
    print(f"Samples: train={len(train_idx)}, val={len(val_idx)}, test={len(test_idx)}")
    print(f"Features: {len(feature_cols)}")

    all_results = {}
    best_model = {"name": None, "val_roc": -1}

    # ── Step 2: Baseline models ──────────────────────────────────────────
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier

    baselines = {
        "logistic_regression": LogisticRegression(
            max_iter=2000, random_state=SEED, class_weight="balanced"
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=500, random_state=SEED, class_weight="balanced", n_jobs=-1
        ),
    }

    for name, model in baselines.items():
        model.fit(X_train, y_train)
        val_proba = model.predict_proba(X_val)[:, 1]
        val_pred = model.predict(X_val)
        test_proba = model.predict_proba(X_test)[:, 1]
        test_pred = model.predict(X_test)
        all_results[f"{name}_val"] = metrics_report(y_val, val_pred, val_proba, f"{name} (val)")
        all_results[f"{name}_test"] = metrics_report(y_test, test_pred, test_proba, f"{name} (test)")
        r = all_results[f"{name}_val"]["roc_auc"] or 0
        if r > best_model["val_roc"]:
            best_model = {"name": name, "val_roc": r}
        print(f"  {name}: val ROC-AUC={r:.4f}")

    # ── Step 3: Neural network ───────────────────────────────────────────
    import torch
    import torch.nn as nn

    torch.manual_seed(SEED)

    from backend.ml.models.arch import GenomicClassifierNet

    model = GenomicClassifierNet(input_dim=len(feature_cols))
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = nn.BCELoss()

    Xtr = torch.tensor(X_train, dtype=torch.float32)
    ytr = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
    Xva = torch.tensor(X_val, dtype=torch.float32)
    yva = torch.tensor(y_val, dtype=torch.float32).unsqueeze(1)

    epochs = 200
    patience = 20
    best_val_loss = float("inf")
    best_state = None
    best_epoch = 0
    history = {"train_loss": [], "val_loss": [], "val_acc": []}

    print(f"\nTraining MLP (343→64→1), epochs={epochs}, patience={patience}, seed={SEED}")

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        out = model(Xtr)
        loss = criterion(out, ytr)
        loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            vout = model(Xva)
            vloss = criterion(vout, yva)
            vacc = ((vout > 0.5).float() == yva).float().mean().item()

        history["train_loss"].append(round(loss.item(), 5))
        history["val_loss"].append(round(vloss.item(), 5))
        history["val_acc"].append(round(vacc, 4))

        if vloss.item() < best_val_loss:
            best_val_loss = vloss.item()
            best_state = {k: v.clone() for k, v in model.state_dict().items()}
            best_epoch = epoch + 1

        if epoch % 20 == 0:
            print(f"  epoch {epoch+1:3d}: train_loss={loss.item():.4f} val_loss={vloss.item():.4f} val_acc={vacc:.4f}")

        # early stopping
        if epoch - best_epoch > patience:
            print(f"  Early stopping at epoch {epoch+1} (best epoch {best_epoch})")
            break

    # Restore best weights (selected on VALIDATION only)
    model.load_state_dict(best_state)

    # Final evaluation — test set touched only now
    Xte = torch.tensor(X_test, dtype=torch.float32)
    yte = torch.tensor(y_test, dtype=torch.float32).unsqueeze(1)
    model.eval()
    with torch.no_grad():
        val_proba_np = model(Xva).numpy().flatten()
        test_proba_np = model(Xte).numpy().flatten()
    val_pred_np = (val_proba_np > 0.5).astype(int)
    test_pred_np = (test_proba_np > 0.5).astype(int)
    all_results["mlp_val"] = metrics_report(y_val, val_pred_np, val_proba_np, "mlp (val)")
    all_results["mlp_test"] = metrics_report(y_test, test_pred_np, test_proba_np, "mlp (test)")
    if (all_results["mlp_val"]["roc_auc"] or 0) > best_model["val_roc"]:
        best_model = {"name": "mlp", "val_roc": all_results["mlp_val"]["roc_auc"]}
    print(f"  MLP best epoch {best_epoch} (val loss {best_val_loss:.4f})")

    # ── Step 4/6: Reproducibility + artifacts ────────────────────────────
    import torchvision, sklearn, numpy as np_ver
    config = {
        "experiment": "genomic_pathogenic_vs_commensal",
        "target": "Epidemiology (pathogenic=1, commensal=0)",
        "inputs": "343 genomic features (340 kmer + sequence_length + GC_fraction + N_fraction)",
        "split": {"train": len(train_idx), "val": len(val_idx), "test": len(test_idx)},
        "split_level": "isolate",
        "seed": SEED,
        "hyperparameters": {
            "logistic_regression": {"max_iter": 2000, "class_weight": "balanced"},
            "random_forest": {"n_estimators": 500, "class_weight": "balanced"},
            "mlp": {"architecture": "343-64-1", "lr": 1e-3, "weight_decay": 1e-4,
                    "epochs": epochs, "patience": patience, "best_epoch": best_epoch,
                    "early_stopping": f"val_loss patience={patience}"},
        },
        "best_model_by_val_roc": best_model["name"],
        "dependencies": {
            "torch": torch.__version__,
            "torchvision": torchvision.__version__,
            "numpy": np_ver.__version__,
            "pandas": pd.__version__,
            "scikit-learn": sklearn.__version__,
        },
    }

    # Save feature schema
    with open(ARTIFACT_DIR / "feature_schema.json", "w") as f:
        json.dump({"feature_count": len(feature_cols), "features": feature_cols,
                   "id_columns": ID_COLS, "target": TARGET_COL}, f, indent=2)

    # Save split sample IDs
    with open(ARTIFACT_DIR / "split_sample_ids.json", "w") as f:
        json.dump({name: [str(df["Identifier"].iloc[i]) for i in idx] for name, idx in split_idx.items()}, f, indent=2)

    # Save model weights
    torch.save({
        "model_state": best_state,
        "architecture": "GenomicClassifierNet(343-64-1)",
        "seed": SEED,
        "feature_schema": "feature_schema.json",
        "best_epoch": best_epoch,
        "scaler": {"mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist()},
    }, ARTIFACT_DIR / "genomic_classifier_best.pt")

    # Save scaler separately for the inference interface
    with open(ARTIFACT_DIR / "feature_scaler.json", "w") as f:
        json.dump({"mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist()}, f)

    # Save metrics + history + config
    with open(ARTIFACT_DIR / "metrics.json", "w") as f:
        json.dump(all_results, f, indent=2)
    with open(ARTIFACT_DIR / "training_history.json", "w") as f:
        json.dump(history, f, indent=2)
    with open(ARTIFACT_DIR / "experiment_config.json", "w") as f:
        json.dump(config, f, indent=2)

    # ── Step 5: Final report ─────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("FINAL RESULTS — untouched TEST set")
    print("=" * 70)
    for key in ["logistic_regression_test", "random_forest_test", "mlp_test"]:
        r = all_results[key]
        print(f"\n  {r['model']}:")
        print(f"    accuracy={r['accuracy']}  precision={r['precision']}  recall={r['recall']}  F1={r['f1']}  ROC-AUC={r['roc_auc']}")
        print(f"    confusion matrix (rows=true, cols=pred): {r['confusion_matrix']}")

    print("\n  Selected model (by validation ROC-AUC):", best_model["name"])

    print("\n" + "=" * 70)
    print("LIMITATIONS — THIS PREDICTS PATHOGENIC vs COMMENSAL STATUS")
    print("It does NOT predict biofilm infection. No clinical claim is made.")
    print("=" * 70)
    print(f"\nArtifacts saved to: {ARTIFACT_DIR}")


if __name__ == "__main__":
    sys.path.insert(0, "/home/user/biofilm-ai")
    main()
