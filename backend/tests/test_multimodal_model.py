"""
BiofilmAI — Multimodal architecture scaffold unit tests.

Run:
    python -m backend.tests.test_multimodal_model

Covers:
  1. all modalities present
  2. only genomics present
  3. genomics + clinical
  4. missing microscopy
  5. missing spectroscopy
  6. missing genomics
  7. all modalities missing -> fails clearly
  8. incorrect tensor dimensions -> fails
  9. modality mask correctness
  + untrained state (model_mode / predict refusal)
"""

from __future__ import annotations

import os
import sys

# The check marks below need UTF-8; the Windows console defaults to cp1252.
sys.stdout.reconfigure(encoding="utf-8")

try:
    import torch
except ImportError:
    # PyTorch is only in backend/ml/requirements-ml.txt; the demo server does not need it.
    print("SKIPPED: PyTorch is not installed. Install it with:")
    print("    pip install -r backend/ml/requirements-ml.txt")
    sys.exit(0)

# Keep single-threaded to stay within the sandbox memory budget
torch.set_num_threads(1)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from backend.ml.models.multimodal_model import MultimodalModel, MODEL_MODE

PASS = 0
FAIL = 0


def check(name: str, ok: bool, detail: str = ""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  ✅ PASS: {name}")
    else:
        FAIL += 1
        print(f"  ❌ FAIL: {name} — {detail}")


def tensors(batch: int = 2):
    """Build valid tensors for all four modalities.

    Sequence lengths are kept short (the encoders accept variable-length
    sequences) so the tests stay memory-light in the sandbox.
    """
    return {
        "microscopy": torch.randn(batch, 3, 224, 224),
        "spectroscopy": torch.randn(batch, 64, 2),
        "genomics": torch.randint(0, 4, (batch, 64)),
        "genomics_mask": torch.ones(batch, 64, dtype=torch.bool),
        "clinical": torch.randn(batch, 32),
    }


def run_forward(model, present, data, batch=2):
    kwargs = {
        "microscopy": data["microscopy"] if present.get("microscopy") else None,
        "spectroscopy": data["spectroscopy"] if present.get("spectroscopy") else None,
        "genomics": data["genomics"] if present.get("genomics") else None,
        "genomics_mask": data["genomics_mask"] if present.get("genomics") else None,
        "clinical": data["clinical"] if present.get("clinical") else None,
        "modalities_present": present,
    }
    return model(**kwargs)


def main():
    print("=" * 66)
    print("BiofilmAI — Multimodal Architecture Scaffold Tests")
    print("=" * 66)
    model = MultimodalModel()
    data = tensors()

    ALL = {m: True for m in ["microscopy", "spectroscopy", "genomics", "clinical"]}

    # ── 1. All modalities present ─────────────────────────────────────────
    out = run_forward(model, ALL, data)
    check("all modalities present runs", out["unified_representation"].shape[0] == 2,
          str(out["unified_representation"].shape))
    check("unified representation is 128-dim", out["unified_representation"].shape[1] == 128)
    check("all four modality embeddings produced",
          set(out["modality_embeddings"].keys()) == set(ALL.keys()))

    # ── 2. Only genomics present ──────────────────────────────────────────
    present_g = {m: False for m in ALL}; present_g["genomics"] = True
    out = run_forward(model, present_g, data)
    check("only genomics present runs",
          set(out["modality_embeddings"].keys()) == {"genomics"},
          str(out["modality_embeddings"].keys()))

    # ── 3. Genomics + clinical ────────────────────────────────────────────
    present_gc = {m: False for m in ALL}; present_gc["genomics"] = True; present_gc["clinical"] = True
    out = run_forward(model, present_gc, data)
    check("genomics + clinical present",
          set(out["modality_embeddings"].keys()) == {"genomics", "clinical"},
          str(out["modality_embeddings"].keys()))

    # ── 4/5/6. Missing each modality in turn ──────────────────────────────
    for missing in ["microscopy", "spectroscopy", "genomics", "clinical"]:
        present = dict(ALL); present[missing] = False
        out = run_forward(model, present, data)
        check(f"missing {missing} still runs (batch {out['batch_size']})",
              missing not in out["modality_embeddings"], str(out["modality_embeddings"].keys()))

    # ── 7. All modalities missing -> clear failure ────────────────────────
    none_present = {m: False for m in ALL}
    try:
        run_forward(model, none_present, data)
        check("all modalities missing fails clearly", False, "no exception raised")
    except ValueError as e:
        check("all modalities missing fails clearly", "ALL MODALITIES MISSING" in str(e), str(e))

    # modalities_present omitted entirely -> clear failure
    try:
        model(**{k: (data[k] if k in ("microscopy",) else None) for k in ["microscopy"]})
        check("missing modalities_present arg fails", False)
    except ValueError as e:
        check("missing modalities_present arg fails", "modalities_present is required" in str(e), str(e))

    # ── 8. Incorrect tensor dimensions ────────────────────────────────────
    bad = dict(data); bad["clinical"] = torch.randn(2, 31)   # wrong last dim
    try:
        run_forward(model, ALL, bad)
        check("wrong clinical dims fail", False)
    except ValueError as e:
        check("wrong clinical dims fail", "clinical" in str(e), str(e))

    bad = dict(data); bad["microscopy"] = torch.randn(2, 3, 100, 100)  # wrong spatial size
    try:
        run_forward(model, ALL, bad)
        check("wrong microscopy size fails", False)
    except ValueError as e:
        check("wrong microscopy size fails", "microscopy" in str(e), str(e))

    bad = dict(data); bad["genomics"] = torch.randn(2, 64)  # float, not integer tokens
    try:
        run_forward(model, ALL, bad)
        check("float genomics tokens fail", False)
    except ValueError as e:
        check("float genomics tokens fail", "integer" in str(e), str(e))

    # batch mismatch
    bad = dict(data); bad["clinical"] = torch.randn(3, 32)
    try:
        run_forward(model, ALL, bad)
        check("batch mismatch fails", False)
    except ValueError as e:
        check("batch mismatch fails", "Batch mismatch" in str(e), str(e))

    # presence flag vs tensor inconsistency: microscopy flag True (with tensor),
    # clinical flag False but clinical tensor passed anyway
    present_mismatch = {m: False for m in ALL}
    present_mismatch["microscopy"] = True   # keep one present so presence check passes
    try:
        model(microscopy=data["microscopy"], clinical=data["clinical"],
              modalities_present=present_mismatch)
        check("flag/tensor inconsistency fails", False)
    except ValueError as e:
        check("flag/tensor inconsistency fails", "clinical" in str(e), str(e))

    # ── 9. Modality mask correctness ──────────────────────────────────────
    out = run_forward(model, present_g, data)
    contrib = out["contributions"]
    check("absent modalities have zero contribution",
          contrib["microscopy"] == 0.0 and contrib["spectroscopy"] == 0.0 and contrib["clinical"] == 0.0,
          str(contrib))
    check("present modality has positive contribution", contrib["genomics"] > 0.0, str(contrib))

    # ── Untrained state ───────────────────────────────────────────────────
    check("model_mode is untrained_multimodal", out["model_mode"] == MODEL_MODE, out["model_mode"])
    check("prediction is None (no fake output)", out["prediction"] is None)
    try:
        model.predict(**{k: data[k] for k in ["microscopy"]})
        check("predict() refuses untrained model", False)
    except RuntimeError as e:
        check("predict() refuses untrained model", "UNTRAINED" in str(e), str(e))

    print("=" * 66)
    print(f"  PASSED: {PASS}   FAILED: {FAIL}")
    print("=" * 66)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
