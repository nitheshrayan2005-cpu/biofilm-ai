"""
BiofilmAI — Inference Script
===============================

CLI entry point for running the real model on one or more samples.

Usage:
    python -m backend.ml.inference.run_inference \
        --weights weights/biofilm_model.pt \
        --sample-info '{"sampleId":"S-001","studyId":"S","sampleType":"Wound swab"}' \
        --clinical '{"infectionContext":"chronic-wound"}' \
        --microscopy path/to/image.png \
        --spectroscopy path/to/spectra.csv \
        --genomics path/to/sequence.fasta

If no weights are available, prints the honest status and exits.
"""

from __future__ import annotations

import argparse
import json
import os
import sys


def main():
    parser = argparse.ArgumentParser(description="Run the BiofilmAI real model")
    parser.add_argument("--weights", type=str, default="weights/biofilm_model.pt")
    parser.add_argument("--sample-info", type=str, required=True,
                        help='JSON string: {"sampleId":..., "studyId":..., "sampleType":...}')
    parser.add_argument("--clinical", type=str, default="{}",
                        help='JSON string of clinical data')
    parser.add_argument("--microscopy", type=str, default=None, help="Path to microscopy image")
    parser.add_argument("--spectroscopy", type=str, default=None, help="Path to spectroscopy file")
    parser.add_argument("--genomics", type=str, default=None, help="Path to genomics file")
    parser.add_argument("--device", type=str, default="cpu")
    args = parser.parse_args()

    # ── Guard ────────────────────────────────────────────────────────────
    if not os.path.isfile(args.weights):
        print("=" * 70)
        print("NO TRAINED MODEL WEIGHTS AVAILABLE — MODEL REMAINS IN DEMO MODE.")
        print(f"Weights expected at: {os.path.abspath(args.weights)}")
        print("=" * 70)
        sys.exit(1)

    # ── Load model ───────────────────────────────────────────────────────
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    from backend.ml.model_loader import build_model, load_weights
    from backend.ml.model_config import default_config

    config = default_config()
    config.device = args.device
    model = build_model(config)
    if not load_weights(model, args.weights, device=args.device):
        print(f"Failed to load weights from {args.weights}")
        sys.exit(1)
    model.to(args.device)
    model.eval()

    # ── Preprocess inputs ────────────────────────────────────────────────
    from backend.ml.preprocessing.microscopy import preprocess_microscopy
    from backend.ml.preprocessing.spectroscopy import preprocess_spectroscopy
    from backend.ml.preprocessing.genomics import preprocess_genomics
    from backend.ml.preprocessing.clinical import preprocess_clinical

    microscopy_t = None
    spectroscopy_t = None
    genomics_t = None
    genomics_mask = None
    clinical_t = None
    modality_mask = {}

    if args.microscopy and os.path.isfile(args.microscopy):
        with open(args.microscopy, "rb") as f:
            microscopy_t = preprocess_microscopy(f.read(), device=args.device)
        if microscopy_t is not None:
            modality_mask["microscopy"] = __import__("torch").ones(1, dtype=__import__("torch").bool)

    if args.spectroscopy and os.path.isfile(args.spectroscopy):
        with open(args.spectroscopy, "rb") as f:
            spectroscopy_t = preprocess_spectroscopy(f.read(), device=args.device)
        if spectroscopy_t is not None:
            modality_mask["spectroscopy"] = __import__("torch").ones(1, dtype=__import__("torch").bool)

    if args.genomics and os.path.isfile(args.genomics):
        with open(args.genomics, "rb") as f:
            result = preprocess_genomics(f.read(), device=args.device)
        if result is not None:
            genomics_t, genomics_mask = result
            modality_mask["genomics"] = __import__("torch").ones(1, dtype=__import__("torch").bool)

    clinical_data = json.loads(args.clinical)
    clinical_t = preprocess_clinical(clinical_data, device=args.device)
    if clinical_t is not None:
        modality_mask["clinical"] = __import__("torch").ones(1, dtype=__import__("torch").bool)

    # ── Run ──────────────────────────────────────────────────────────────
    import torch
    output = model.predict(
        microscopy=microscopy_t,
        spectroscopy=spectroscopy_t,
        genomics=genomics_t,
        genomics_mask=genomics_mask,
        clinical=clinical_t,
        modality_mask=modality_mask,
    )

    prob = output["prediction"].item()
    category = output["risk_category"][0]

    print("=" * 60)
    print("Real Model Inference Result")
    print("=" * 60)
    print(f"  Biofilm probability : {prob:.4f}")
    print(f"  Risk category       : {category}")
    print(f"  Available modalities: {list(modality_mask.keys())}")
    print(f"  Contributions       : {json.dumps(output['contributions'])}")
    print("=" * 60)
    print("NOTE: This is a model-estimated probability from the real trained model.")
    print("It is not a clinical diagnosis.")


if __name__ == "__main__":
    main()
