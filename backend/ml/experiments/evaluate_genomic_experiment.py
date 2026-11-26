"""
BiofilmAI — Genomic Experiment: Evaluation & Interpretability
================================================================

Follows the first real training experiment. Uses the SAME 103-isolate
dataset, SAME untouched 16-isolate test split.

Stage 1 — Robustness: stratified 5-fold CV on the 72-isolate training
         portion ONLY (test set never used for selection).
Stage 2 — Uncertainty: per-isolate LR probabilities on the untouched
         test set (no invented confidence intervals).
Stage 3 — Feature interpretability: LR coefficients + RF importance.
Stage 4 — Error analysis on the untouched test set.
Stage 5 — Visualizations saved to backend/ml/artifacts/.

Target: Epidemiology = pathogenic vs commensal (NOT biofilm infection).
"""

from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

FEATURES_CSV = "/home/user/uploads/BiofilmAI_genomic_features.csv"
SPLITS_JSON = "/home/user/biofilm-ai/dataset/audit/splits.json"
ART = Path("/home/user/biofilm-ai/backend/ml/artifacts")

ID_COLS = ["Identifier", "genome_file"]
TARGET_COL = "Epidemiology"
NON_KMER = ["sequence_length", "GC_fraction", "N_fraction"]


def load():
    df = pd.read_csv(FEATURES_CSV)
    splits = json.load(open(SPLITS_JSON))
    kmer_cols = sorted([c for c in df.columns if c.startswith("kmer_")])
    feats = kmer_cols + NON_KMER
    assert len(feats) == 343
    X = df[feats].to_numpy(dtype=np.float32)
    y = (df[TARGET_COL].astype(str).str.strip().str.lower() == "pathogenic").astype(int).to_numpy()
    id_map = {str(i): idx for idx, i in enumerate(df["Identifier"].astype(str))}
    idx = {n: [id_map[i] for i in ids] for n, ids in splits.items()}
    return df, feats, X, y, idx


def summarize(y_true, y_pred, y_proba):
    from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                                 f1_score, roc_auc_score)
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_true, y_proba) if len(set(y_true)) > 1 else np.nan,
    }


def main():
    df, feats, X, y, idx = load()
    train_idx, val_idx, test_idx = idx["train"], idx["val"], idx["test"]

    from sklearn.preprocessing import StandardScaler
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import StratifiedKFold

    scaler = StandardScaler().fit(X[train_idx])
    Xs = scaler.transform(X)

    X_train, y_train = Xs[train_idx], y[train_idx]
    X_test, y_test = Xs[test_idx], y[test_idx]
    X_val, y_val = Xs[val_idx], y[val_idx]

    # ═══ 1. Stratified CV on training portion only (72 isolates) ═════════
    print("=" * 70)
    print("STAGE 1 — Stratified 5-fold CV on the 72-isolate training portion")
    print("=" * 70)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    cv_results = {}
    models = {
        "logistic_regression": LogisticRegression(max_iter=2000, random_state=SEED, class_weight="balanced"),
        "random_forest": RandomForestClassifier(n_estimators=500, random_state=SEED, class_weight="balanced", n_jobs=-1),
    }
    for name, model in models.items():
        fold_metrics = {m: [] for m in ["accuracy", "precision", "recall", "f1", "roc_auc"]}
        for tr, va in cv.split(X_train, y_train):
            model.fit(X_train[tr], y_train[tr])
            proba = model.predict_proba(X_train[va])[:, 1]
            pred = model.predict(X_train[va])
            m = summarize(y_train[va], pred, proba)
            for k in fold_metrics:
                fold_metrics[k].append(m[k])
        cv_results[name] = {
            k: {"mean": round(float(np.nanmean(v)), 4), "std": round(float(np.nanstd(v)), 4)}
            for k, v in fold_metrics.items()
        }
        print(f"\n  {name} (CV mean ± std):")
        for k, v in cv_results[name].items():
            print(f"    {k:10s}: {v['mean']:.4f} ± {v['std']:.4f}")

    with open(ART / "cross_validation_metrics.json", "w") as f:
        json.dump(cv_results, f, indent=2)

    # ═══ 2+4. Selected model (LR) — test predictions + error analysis ════
    print("\n" + "=" * 70)
    print("STAGE 2+4 — Selected model (LR): test predictions + errors")
    print("=" * 70)
    lr = LogisticRegression(max_iter=2000, random_state=SEED, class_weight="balanced")
    lr.fit(X_train, y_train)  # fit on train only; test untouched until now
    test_proba = lr.predict_proba(X_test)[:, 1]
    test_pred = (test_proba >= 0.5).astype(int)

    test_ids = [str(df["Identifier"].iloc[i]) for i in test_idx]
    pred_table = pd.DataFrame({
        "isolate_id": test_ids,
        "true_label": ["pathogenic" if y == 1 else "commensal" for y in y_test],
        "predicted_label": ["pathogenic" if p == 1 else "commensal" for p in test_pred],
        "pathogenic_probability": np.round(test_proba, 4),
        "correct": (test_pred == y_test).astype(int),
    })
    pred_table.to_csv(ART / "test_predictions.csv", index=False)

    # Per-isolate top contributing features for LR (coef * scaled feature)
    coef = lr.coef_[0]
    contrib = X_test * coef  # (n_test, 343)
    top_pos = np.argsort(-contrib, axis=1)[:, :5]
    pred_table["top_features"] = [
        "; ".join(f"{feats[j]}({contrib[i,j]:+.3f})" for j in top_pos[i]) for i in range(len(test_ids))
    ]

    error_table = pred_table[pred_table["correct"] == 0].copy()
    error_table.to_csv(ART / "error_analysis.csv", index=False)

    fp = error_table[(error_table["true_label"] == "commensal") & (error_table["predicted_label"] == "pathogenic")]
    fn = error_table[(error_table["true_label"] == "pathogenic") & (error_table["predicted_label"] == "commensal")]
    print(f"\n  Test errors: {len(error_table)}/{len(test_ids)}")
    print(f"  False positives (commensal→pathogenic): {len(fp)}")
    print(f"  False negatives (pathogenic→commensal): {len(fn)}")
    for _, r in error_table.iterrows():
        print(f"    {r['isolate_id']}: true={r['true_label']:11s} pred={r['predicted_label']:11s} "
              f"P(path)={r['pathogenic_probability']:.3f}")

    # ═══ 3. Feature interpretability ═════════════════════════════════════
    print("\n" + "=" * 70)
    print("STAGE 3 — Feature interpretability")
    print("=" * 70)
    lr_table = pd.DataFrame({"feature": feats, "coefficient": coef})
    lr_table["abs_coefficient"] = lr_table["coefficient"].abs()
    lr_table = lr_table.sort_values("abs_coefficient", ascending=False)
    lr_table.to_csv(ART / "logistic_coefficients.csv", index=False)

    rf = RandomForestClassifier(n_estimators=500, random_state=SEED, class_weight="balanced", n_jobs=-1)
    rf.fit(X_train, y_train)
    rf_table = pd.DataFrame({"feature": feats, "importance": rf.feature_importances_})
    rf_table = rf_table.sort_values("importance", ascending=False)
    rf_table.to_csv(ART / "random_forest_importance.csv", index=False)

    print("\n  Top 10 LR features (coefficient, scaled features):")
    for _, r in lr_table.head(10).iterrows():
        print(f"    {r['feature']:12s}  coef={r['coefficient']:+.4f}")
    print("\n  Top 10 RF features (importance):")
    for _, r in rf_table.head(10).iterrows():
        print(f"    {r['feature']:12s}  imp={r['importance']:.5f}")

    # ═══ 5. Visualizations ══════════════════════════════════════════════
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve, auc, confusion_matrix, ConfusionMatrixDisplay

    print("\n" + "=" * 70)
    print("STAGE 5 — Generating figures")
    print("=" * 70)

    # ROC curves (LR + RF on test)
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    for name, model in [("Logistic Regression", lr), ("Random Forest", rf)]:
        proba = model.predict_proba(X_test)[:, 1]
        fpr, tpr, _ = roc_curve(y_test, proba)
        ax.plot(fpr, tpr, label=f"{name} (AUC={auc(fpr, tpr):.3f})")
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4)
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC — untouched test set (16 isolates)")
    ax.legend()
    fig.tight_layout(); fig.savefig(ART / "roc_curve.png", dpi=150); plt.close(fig)

    # Confusion matrix (LR)
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ConfusionMatrixDisplay.from_predictions(y_test, test_pred,
        display_labels=["commensal", "pathogenic"], ax=ax, cmap="Blues")
    ax.set_title("LR confusion matrix — test set")
    fig.tight_layout(); fig.savefig(ART / "confusion_matrix.png", dpi=150); plt.close(fig)

    # CV performance plot
    fig, ax = plt.subplots(figsize=(6, 3.5))
    metrics_keys = ["accuracy", "precision", "recall", "f1", "roc_auc"]
    x = np.arange(len(metrics_keys)); w = 0.38
    for j, (name, color) in enumerate([("logistic_regression", "#176B87"), ("random_forest", "#2A9D8F")]):
        means = [cv_results[name][k]["mean"] for k in metrics_keys]
        stds = [cv_results[name][k]["std"] for k in metrics_keys]
        ax.bar(x + (j - 0.5) * w, means, w, yerr=stds, label=name, color=color, capsize=3)
    ax.set_xticks(x); ax.set_xticklabels(metrics_keys, rotation=20)
    ax.set_ylabel("score"); ax.set_ylim(0, 1.05)
    ax.set_title("5-fold CV on training portion (72 isolates)")
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(ART / "cross_validation_performance.png", dpi=150); plt.close(fig)

    # LR feature importance plot (top 20)
    fig, ax = plt.subplots(figsize=(6, 5))
    top = lr_table.head(20).iloc[::-1]
    ax.barh(top["feature"], top["coefficient"], color=["#C94C4C" if c < 0 else "#176B87" for c in top["coefficient"]])
    ax.set_xlabel("standardized coefficient")
    ax.set_title("LR top-20 features (pathogenic direction + / commensal −)")
    fig.tight_layout(); fig.savefig(ART / "logistic_feature_importance.png", dpi=150); plt.close(fig)

    # RF feature importance plot (top 20)
    fig, ax = plt.subplots(figsize=(6, 5))
    top = rf_table.head(20).iloc[::-1]
    ax.barh(top["feature"], top["importance"], color="#2A9D8F")
    ax.set_xlabel("importance")
    ax.set_title("RF top-20 features")
    fig.tight_layout(); fig.savefig(ART / "random_forest_importance.png", dpi=150); plt.close(fig)

    # Probability distribution by class (LR, test)
    fig, ax = plt.subplots(figsize=(5.5, 4))
    for cls, color, label in [(1, "#C94C4C", "pathogenic"), (0, "#2E8B72", "commensal")]:
        p = test_proba[y_test == cls]
        if len(p):
            ax.hist(p, bins=8, alpha=0.55, color=color, label=f"{label} (n={len(p)})")
    ax.axvline(0.5, color="k", ls="--", lw=1)
    ax.set_xlabel("LR pathogenic probability"); ax.set_ylabel("count")
    ax.set_title("Probability distribution by class — test set")
    ax.legend()
    fig.tight_layout(); fig.savefig(ART / "probability_distribution.png", dpi=150); plt.close(fig)

    # ═══ Save compact evaluation summary ═════════════════════════════════
    final_lr = summarize(y_test, test_pred, test_proba)
    summary = {
        "cv_5fold_training_portion": cv_results,
        "selected_model": "logistic_regression",
        "test_metrics_lr": {k: round(float(v), 4) for k, v in final_lr.items()},
        "test_errors": {"total": int(len(error_table)), "fp": int(len(fp)), "fn": int(len(fn))},
    }
    with open(ART / "evaluation_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "=" * 70)
    print("DONE — artifacts saved to", ART)
    print("=" * 70)


if __name__ == "__main__":
    sys.path.insert(0, "/home/user/biofilm-ai")
    main()
