"""
BiofilmAI — Evaluation Script
===============================

CLI entry point for evaluating the real multimodal model on a held-out
test set.

Refuses to report metrics on fabricated or missing data. If no dataset
or weights are provided it prints the honest status and exits.

Usage:
    python -m backend.ml.evaluation.evaluate_model \
        --dataset ./dataset \
        --weights weights/biofilm_model.pt
"""

from __future__ import annotations

import argparse
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Evaluate the BiofilmAI multimodal model")
    parser.add_argument("--dataset", type=str, default="./dataset")
    parser.add_argument("--weights", type=str, default="weights/biofilm_model.pt")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--json", action="store_true", help="Emit metrics as JSON")
    args = parser.parse_args()

    # ── Guards ───────────────────────────────────────────────────────────
    if not os.path.isdir(args.dataset):
        print("NO REAL DATASET AVAILABLE — MODEL REMAINS IN DEMO MODE.")
        sys.exit(1)
    if not os.path.isfile(args.weights):
        print(f"No trained weights at {args.weights}. Cannot evaluate.")
        print("No evaluation metrics are reported because no model has been trained.")
        sys.exit(1)

    # ── Load ─────────────────────────────────────────────────────────────
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    from backend.ml.data.dataloader import get_dataloaders
    from backend.ml.model_loader import build_model, load_weights
    from backend.ml.model_config import default_config
    from backend.ml.evaluation.evaluator import Evaluator

    loaders = get_dataloaders(dataset_root=args.dataset, batch_size=args.batch_size, data_available=True)
    if loaders["test"] is None:
        print("No test split found in the dataset. Add a test split and retry.")
        sys.exit(1)

    config = default_config()
    config.device = args.device
    model = build_model(config)
    if not load_weights(model, args.weights, device=args.device):
        print(f"Failed to load weights from {args.weights}")
        sys.exit(1)
    model.to(args.device)

    # ── Evaluate ─────────────────────────────────────────────────────────
    evaluator = Evaluator(model, device=args.device)
    metrics = evaluator.evaluate(loaders["test"])

    if args.json:
        print(json.dumps(metrics, indent=2))
    else:
        print("=" * 60)
        print("Evaluation Results (held-out test set)")
        print("=" * 60)
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"  {key:20s}: {value:.4f}")
            else:
                print(f"  {key:20s}: {value}")
        print("=" * 60)
        print("These metrics were computed on a real held-out test set.")
        print("They are NOT demo values.")


if __name__ == "__main__":
    main()
