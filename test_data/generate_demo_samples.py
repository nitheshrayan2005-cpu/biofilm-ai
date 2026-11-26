"""
BiofilmAI — Generate 5 synthetic demo cases.

Run from the project root:
    .venv\\Scripts\\python.exe test_data\\generate_demo_samples.py

Writes test_data/demo_samples/case_N_<name>/ with:
    microscopy.png        upload as Microscopy
    spectroscopy.csv      upload as Spectroscopy
    spectrum_preview.png  picture of the spectrum (for slides)
    genomics.fasta        upload as Genomics

All data is SYNTHETIC and for demonstration only.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent / "demo_samples"
SIZE = 512

# name, title, microscopy params, spectrum band weights, organism, GC fraction
CASES = [
    {
        "dir": "case_1_mature_implant_biofilm",
        "title": "Mature S. epidermidis biofilm - knee implant",
        "clusters": 18, "cluster_cells": (120, 220), "spread": 26, "planktonic": 120,
        "dead_frac": 0.08, "rods": 0.0, "eps": True,
        "bands": {"eps": 1.6, "protein": 1.0, "nucleic": 1.1, "lipid": 0.9},
        "organism": "Staphylococcus epidermidis", "gc": 0.32,
    },
    {
        "dir": "case_2_early_attachment",
        "title": "Early attachment - catheter tip (6 h)",
        "clusters": 6, "cluster_cells": (15, 35), "spread": 12, "planktonic": 260,
        "dead_frac": 0.05, "rods": 0.0, "eps": False,
        "bands": {"eps": 0.4, "protein": 1.0, "nucleic": 0.9, "lipid": 0.8},
        "organism": "Staphylococcus aureus", "gc": 0.33,
    },
    {
        "dir": "case_3_planktonic_no_biofilm",
        "title": "Planktonic cells only - no biofilm",
        "clusters": 0, "cluster_cells": (0, 0), "spread": 0, "planktonic": 380,
        "dead_frac": 0.12, "rods": 1.0, "eps": False,
        "bands": {"eps": 0.15, "protein": 1.1, "nucleic": 1.0, "lipid": 0.7},
        "organism": "Escherichia coli", "gc": 0.51,
    },
    {
        "dir": "case_4_mixed_species_wound",
        "title": "Mixed-species chronic wound biofilm",
        "clusters": 14, "cluster_cells": (90, 170), "spread": 30, "planktonic": 150,
        "dead_frac": 0.15, "rods": 0.5, "eps": True,
        "bands": {"eps": 1.3, "protein": 1.2, "nucleic": 1.0, "lipid": 1.1},
        "organism": "Pseudomonas aeruginosa", "gc": 0.66,
    },
    {
        "dir": "case_5_antibiotic_treated",
        "title": "Biofilm after antibiotic treatment (live/dead)",
        "clusters": 12, "cluster_cells": (80, 150), "spread": 24, "planktonic": 90,
        "dead_frac": 0.55, "rods": 0.0, "eps": True,
        "bands": {"eps": 1.2, "protein": 0.7, "nucleic": 0.6, "lipid": 0.8},
        "organism": "Staphylococcus epidermidis", "gc": 0.32,
    },
]


def _font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


# ── Microscopy ──────────────────────────────────────────────────────────

def _cell(draw: ImageDraw.ImageDraw, x: float, y: float, dead: bool, rod: bool) -> None:
    colour = (random.randint(170, 255), 30, 40) if dead else (30, random.randint(160, 255), 70)
    if rod:
        a = random.uniform(0, math.pi)
        dx, dy = 5 * math.cos(a), 5 * math.sin(a)
        draw.line((x - dx, y - dy, x + dx, y + dy), fill=colour, width=4)
    else:
        r = random.uniform(2.2, 3.6)
        draw.ellipse((x - r, y - r, x + r, y + r), fill=colour)


def make_microscopy(case: dict, path: Path) -> None:
    img = Image.new("RGB", (SIZE, SIZE), (5, 7, 12))
    if case["eps"]:
        # Diffuse blue EPS matrix stain under the clusters
        eps = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
        ed = ImageDraw.Draw(eps)
        for _ in range(case["clusters"] * 2):
            cx, cy = random.randint(0, SIZE), random.randint(0, SIZE)
            r = random.randint(40, 90)
            ed.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(10, 25, 70))
        img = Image.blend(img, eps.filter(ImageFilter.GaussianBlur(25)), 0.9)
    draw = ImageDraw.Draw(img)
    for _ in range(case["clusters"]):
        cx, cy = random.randint(30, SIZE - 30), random.randint(30, SIZE - 30)
        for _ in range(random.randint(*case["cluster_cells"])):
            _cell(draw, cx + random.gauss(0, case["spread"]), cy + random.gauss(0, case["spread"]),
                  random.random() < case["dead_frac"], random.random() < case["rods"])
    for _ in range(case["planktonic"]):
        _cell(draw, random.uniform(0, SIZE), random.uniform(0, SIZE),
              random.random() < case["dead_frac"], random.random() < case["rods"])
    img = img.filter(ImageFilter.GaussianBlur(1.0))

    # Scale bar + caption
    draw = ImageDraw.Draw(img)
    draw.rectangle((SIZE - 110, SIZE - 28, SIZE - 30, SIZE - 23), fill=(255, 255, 255))
    draw.text((SIZE - 95, SIZE - 46), "20 um", fill=(255, 255, 255), font=_font(14))
    draw.text((10, 10), "SYNTHETIC - " + case["title"], fill=(220, 220, 220), font=_font(13))
    img.save(path)


# ── Spectroscopy ────────────────────────────────────────────────────────

# Raman bands (cm^-1): (centre, amplitude, width, group)
BANDS = [
    (720, 35, 12, "nucleic"), (783, 30, 10, "nucleic"), (1004, 65, 8, "protein"),
    (1095, 40, 14, "eps"), (1125, 25, 12, "eps"), (1240, 30, 20, "protein"),
    (1340, 40, 18, "nucleic"), (1450, 55, 16, "lipid"), (1660, 55, 20, "protein"),
]


def spectrum(case: dict) -> list[tuple[int, float]]:
    pts = []
    for w in range(400, 1801, 4):
        y = 100 + 0.02 * (w - 400)
        for c, a, s, g in BANDS:
            y += a * case["bands"][g] * math.exp(-((w - c) ** 2) / (2 * s * s))
        pts.append((w, y + random.gauss(0, 1.5)))
    return pts


def make_spectroscopy(case: dict, csv_path: Path, png_path: Path) -> None:
    pts = spectrum(case)
    csv_path.write_text("wavenumber_cm-1,intensity\n" + "\n".join(f"{w},{y:.3f}" for w, y in pts) + "\n")

    W, H, L, R, T, B = 900, 420, 70, 20, 50, 60
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    lo, hi = min(y for _, y in pts), max(y for _, y in pts)
    sx = lambda w: L + (w - 400) / 1400 * (W - L - R)
    sy = lambda y: H - B - (y - lo) / (hi - lo) * (H - T - B)
    d.line((L, H - B, W - R, H - B), fill="black")
    d.line((L, T, L, H - B), fill="black")
    for w in range(400, 1801, 200):
        d.line((sx(w), H - B, sx(w), H - B + 5), fill="black")
        d.text((sx(w) - 14, H - B + 8), str(w), fill="black", font=_font(12))
    d.line([(sx(w), sy(y)) for w, y in pts], fill=(30, 90, 200), width=2)
    for c, label in [(783, "DNA"), (1004, "Phe"), (1095, "EPS"), (1450, "CH2"), (1660, "Amide I")]:
        d.text((sx(c) - 12, T - 18), label, fill=(120, 120, 120), font=_font(11))
    d.text((W / 2 - 80, H - 25), "Raman shift (cm-1)", fill="black", font=_font(13))
    d.text((8, T - 40), "SYNTHETIC - " + case["title"], fill="black", font=_font(14))
    d.text((8, H / 2), "Intensity", fill="black", font=_font(12))
    img.save(png_path)


# ── Genomics ────────────────────────────────────────────────────────────

def make_fasta(case: dict, path: Path, n_contigs: int = 4, contig_len: int = 5000) -> None:
    gc = case["gc"]
    weights = [(1 - gc) / 2, gc / 2, gc / 2, (1 - gc) / 2]
    org = case["organism"].replace(" ", "_")
    lines = []
    for i in range(1, n_contigs + 1):
        seq = "".join(random.choices("ACGT", weights=weights, k=contig_len))
        lines.append(f">{org}_demo_contig_{i} synthetic GC={gc:.2f} length={contig_len}")
        lines += [seq[j:j + 70] for j in range(0, contig_len, 70)]
    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    random.seed(2026)
    for case in CASES:
        d = OUT / case["dir"]
        d.mkdir(parents=True, exist_ok=True)
        make_microscopy(case, d / "microscopy.png")
        make_spectroscopy(case, d / "spectroscopy.csv", d / "spectrum_preview.png")
        make_fasta(case, d / "genomics.fasta")
        print("wrote", d)
