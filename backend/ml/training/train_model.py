"""
BiofilmAI — Training Script
=============================

CLI entry point for training the real multimodal model.

IMPORTANT: This script refuses to train on fabricated data. It requires a
real labelled dataset directory and will exit with a clear message when
none is available.

Usage:
    python -m backend.ml.training.train_model \
        --dataset ./dataset \
        --epochs 100 \
        --batch-size 32 \
        --lr 1e-4 \
        --out weights/biofilm_model.pt

Prerequisites:
    pip install -r backend/ml/requirements-ml.txt
    A validated dataset (see backend/ml/data/validate_dataset.py)
"""

from __future__ import annotations

import argparse
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Train the BiofilmAI multimodal model")
    parser.add_argument("--dataset", type=str, default="./dataset",
                        help="Path to the labelled dataset directory")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--out", type=str, default="weights/biofilm_model.pt")
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    # ── Guard: no fake training ──────────────────────────────────────────
    if not os.path.isdir(args.dataset):
        print("=" * 70)
        print("NO REAL DATASET AVAILABLE — MODEL REMAINS IN DEMO MODE.")
        print(f"Expected dataset at: {os.path.abspath(args.dataset)}")
        print("Provide a validated labelled dataset before training.")
        print("=" * 70)
        sys.exit(1)

    # ── Validate dataset before training ─────────────────────────────────
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    from backend.ml.data.validator import DatasetValidator
    from backend.ml.data.schema import DatasetSpec

    spec = DatasetSpec(dataset_root=args.dataset)
    report = DatasetValidator(args.dataset, spec).validate()
    if report.get("errors"):
        print("Dataset validation FAILED:")
        for err in report["errors"]:
            print(f"  - {err}")
        sys.exit(1)

    n = report["total_samples"]
    pos = report["positive_labels"]
    neg = report["negative_labels"]
    print(f"Dataset OK: {n} samples ({pos} positive / {neg} negative)")
    if n < spec.min_samples:
        print(f"Too few samples ({n} < {spec.min_samples}). Refusing to train.")
        sys.exit(1)

    # ── Load data ────────────────────────────────────────────────────────
    from backend.ml.data.dataloader import get_dataloaders
    from backend.ml.model_loader import build_model
    from backend.ml.model_config import default_config
    from backend.ml.training.trainer import Trainer

    loaders = get_dataloaders(
        dataset_root=args.dataset,
        batch_size=args.batch_size,
        data_available=True,
    )
    if loaders["train"] is None or loaders["val"] is None:
        print("Train/val loaders could not be built. Check the dataset split.")
        sys.exit(1)

    config = default_config()
    config.device = args.device
    model = build_model(config)
    model.to(args.device)

    # ── Train ────────────────────────────────────────────────────────────
    trainer = Trainer(model, device=args.device)
    # Override CLI options
    trainer.config.epochs = args.epochs
    trainer.config.batch_size = args.batch_size
    trainer.config.learning_rate = args.lr
    trainer.config.checkpoint_dir = os.path.dirname(args.out) or "weights"

    history = trainer.train(loaders["train"], loaders["val"])

    # ── Save final weights ───────────────────────────────────────────────
    from backend.ml.model_loader import save_checkpoint
    path = save_checkpoint(
        model=model,
        epoch=trainer.config.epochs,
        metrics=history.get("val_metrics", [{}])[-1] if history.get("val_metrics") else {},
        config=config,
        path=args.out,
    )
    print(f"\nModel saved to {path}")
    print("Next steps:")
    print("  1. Evaluate:  python -m backend.ml.evaluation.evaluate_model --dataset ./dataset --weights " + path)
    print("  2. Enable:    export BIOFILM_DEMO_MODE=false BIOFILM_WEIGHTS_PATH=" + path)
    print("  3. Restart:   python -m uvicorn main:app --port 8000")


if __name__ == "__main__":
    main()
