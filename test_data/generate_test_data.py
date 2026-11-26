"""
BiofilmAI — Generate synthetic end-to-end test data.

Run from the project root:
    .venv\\Scripts\\python.exe test_data\\generate_test_data.py

All files are SYNTHETIC. They exercise the pipeline; they are not real
patient or laboratory data.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
ARTIFACTS = ROOT / "backend" / "ml" / "artifacts"

random.seed(42)


# ── Microscopy: fluorescence-style biofilm image ────────────────────────

def make_microscopy(path: Path) -> None:
    size = 512
    img = Image.new("RGB", (size, size), (6, 8, 14))
    draw = ImageDraw.Draw(img)
    # Dense cell clusters (biofilm microcolonies)
    for _ in range(14):
        cx, cy = random.randint(40, size - 40), random.randint(40, size - 40)
        for _ in range(random.randint(60, 140)):
            x = cx + random.gauss(0, 22)
            y = cy + random.gauss(0, 22)
            r = random.uniform(2, 4)
            g = random.randint(150, 255)
            draw.ellipse((x - r, y - r, x + r, y + r), fill=(20, g, 60))
    # Scattered planktonic cells
    for _ in range(250):
        x, y = random.uniform(0, size), random.uniform(0, size)
        draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(30, 200, 90))
    img.filter(ImageFilter.GaussianBlur(1.2)).save(path)


# ── Spectroscopy: Raman spectrum (wavenumber, intensity) ────────────────

def make_spectroscopy(path: Path) -> None:
    # Typical bacterial / EPS Raman bands (cm^-1)
    peaks = [(720, 40, 12), (783, 30, 10), (1004, 70, 8), (1095, 35, 14),
             (1240, 30, 20), (1340, 45, 18), (1450, 60, 16), (1660, 55, 20)]
    lines = ["wavenumber_cm-1,intensity"]
    for w in range(400, 1801, 4):
        y = 100 + 0.02 * (w - 400)  # fluorescence baseline
        for c, a, s in peaks:
            y += a * math.exp(-((w - c) ** 2) / (2 * s * s))
        y += random.gauss(0, 1.5)
        lines.append(f"{w},{y:.3f}")
    path.write_text("\n".join(lines) + "\n")


# ── Genomics: FASTA with S. epidermidis-like GC content (~32%) ──────────

def make_fasta(path: Path, n_contigs: int = 3, contig_len: int = 6000) -> None:
    weights = [0.34, 0.16, 0.16, 0.34]  # A, C, G, T
    out = []
    for i in range(1, n_contigs + 1):
        seq = "".join(random.choices("ACGT", weights=weights, k=contig_len))
        out.append(f">TEST_ISOLATE_contig_{i} synthetic length={contig_len}")
        out += [seq[j:j + 70] for j in range(0, contig_len, 70)]
    path.write_text("\n".join(out) + "\n")


# ── Genomic research endpoint request (343 features) ────────────────────

def make_genomic_request(path: Path) -> None:
    # Uses the training-set mean of each feature (an "average isolate"),
    # so every value is in a realistic range for the trained model.
    names = json.loads((ARTIFACTS / "feature_schema.json").read_text())["features"]
    means = json.loads((ARTIFACTS / "feature_scaler.json").read_text())["mean"]
    assert len(names) == len(means) == 343
    path.write_text(json.dumps({"features": dict(zip(names, means))}, indent=1))


# ── Thickness endpoint requests ─────────────────────────────────────────

def make_thickness_requests(path: Path) -> None:
    cases = [
        {"time": 0.0, "flow_rate_ul_min": 1, "channel": "FLAT"},
        {"time": 0.5, "flow_rate_ul_min": 5, "channel": "FLAT"},
        {"time": 1.0, "flow_rate_ul_min": 5, "channel": "RC1"},
        {"time": 0.75, "flow_rate_ul_min": 10, "channel": "RT2"},
        {"time": 1.0, "flow_rate_ul_min": 1, "channel": "RT3"},
    ]
    path.write_text(json.dumps(cases, indent=2))


if __name__ == "__main__":
    make_microscopy(HERE / "microscopy_biofilm.png")
    make_spectroscopy(HERE / "spectroscopy_raman.csv")
    make_fasta(HERE / "genomics_isolate.fasta")
    make_genomic_request(HERE / "genomic_predict_request.json")
    make_thickness_requests(HERE / "thickness_requests.json")
    (HERE / "invalid_microscopy.pdf").write_bytes(b"%PDF-1.4\n% not an image\n")
    print("Test data written to", HERE)
