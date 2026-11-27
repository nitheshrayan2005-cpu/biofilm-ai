"""
BiofilmAI Backend — Measured evidence from the uploaded files.

Every number here is computed from the actual upload, so it can be explained
and checked by hand:

  microscopy   surface coverage, live/dead ratio, cell clustering, matrix stain
  spectroscopy Raman peaks with band assignments, polysaccharide (matrix)
               band relative to protein, signal quality
  genomics     assembly statistics, marker genes (mecA, icaADBC), and the
               trained genomic research model
  clinical     recognised biofilm risk factors from the clinical form

combine() turns the per-modality indicators into a transparent, rule-based
evidence score with each modality's contribution. It is NOT an AI prediction
and NOT a diagnosis.
"""

from __future__ import annotations

import base64
import io
import logging
from collections import deque
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)

ARTIFACTS = Path(__file__).resolve().parent / "ml" / "artifacts"


# ── Microscopy ───────────────────────────────────────────────────────────

BLOCK = 4                      # px per grid cell for cluster detection
CLUSTER_MIN = 0.01             # a "cluster" covers >= 1% of the field
COLONY_MIN = 0.0015            # a "micro-colony" covers >= 0.15% of the field


def _label(grid: np.ndarray) -> tuple[np.ndarray, int]:
    """4-connected component labels of a small boolean grid."""
    h, w = grid.shape
    lab = np.zeros((h, w), dtype=np.int32)
    n = 0
    for y0, x0 in zip(*np.nonzero(grid)):
        if lab[y0, x0]:
            continue
        n += 1
        lab[y0, x0] = n
        queue = deque([(y0, x0)])
        while queue:
            y, x = queue.popleft()
            for yy, xx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= yy < h and 0 <= xx < w and grid[yy, xx] and not lab[yy, xx]:
                    lab[yy, xx] = n
                    queue.append((yy, xx))
    return lab, n


def _otsu(gray: np.ndarray) -> int:
    hist, _ = np.histogram(gray, bins=256, range=(0, 256))
    p = hist / max(hist.sum(), 1)
    omega, mu = np.cumsum(p), np.cumsum(p * np.arange(256))
    between = (mu[-1] * omega - mu) ** 2 / (omega * (1 - omega) + 1e-12)
    return int(np.argmax(between))


def analyze_microscopy(data: bytes) -> dict:
    img = Image.open(io.BytesIO(data)).convert("RGB")
    img.thumbnail((1024, 1024))
    rgb = np.asarray(img, dtype=np.float32)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]

    # Fluorescence live/dead stain: green = live, red = dead, blue = matrix (EPS).
    colour = float(np.mean(np.abs(r - g) + np.abs(g - b))) > 6
    if colour:
        live = (g > 70) & (g > r + 25) & (g > b + 15)
        dead = (r > 70) & (r > g + 25) & (r > b + 15)
        cells = live | dead
        matrix = (b > 40) & (b > r + 12) & (b > g + 8) & ~cells
    else:
        gray = rgb.mean(axis=-1)
        cells = gray > max(_otsu(gray), 40)
        live = dead = matrix = None

    h, w = cells.shape
    hb, wb = h // BLOCK, w // BLOCK
    blocks = cells[:hb * BLOCK, :wb * BLOCK].reshape(hb, BLOCK, wb, BLOCK).sum(axis=(1, 3))
    occupied = blocks > 0
    # Bridge the small gaps between neighbouring cells of one cluster.
    grown = occupied.copy()
    grown[1:] |= occupied[:-1]
    grown[:-1] |= occupied[1:]
    grown[:, 1:] |= occupied[:, :-1]
    grown[:, :-1] |= occupied[:, 1:]
    lab, n = _label(grown)
    areas = np.bincount(lab.ravel(), weights=blocks.ravel())[1:] if n else np.zeros(0)
    field = h * w
    total = float(cells.sum())
    cluster_ids = np.nonzero(areas >= CLUSTER_MIN * field)[0] + 1
    colony_ids = np.nonzero((areas >= COLONY_MIN * field) & (areas < CLUSTER_MIN * field))[0] + 1
    largest = float(areas.max()) / field if n else 0.0
    clustered = float(areas[cluster_ids - 1].sum()) / total if total else 0.0
    colonised = float(areas[colony_ids - 1].sum()) / total if total else 0.0

    if clustered >= 0.6 and largest >= 0.05:
        pattern = "dense_clusters"
        pattern_text = "Dense clustered growth, consistent with a structured biofilm"
    elif clustered + colonised >= 0.3:
        pattern = "micro_colonies"
        pattern_text = "Small micro-colonies, consistent with early attachment"
    else:
        pattern = "scattered"
        pattern_text = "Mostly single scattered cells, consistent with free-floating (planktonic) bacteria"

    result = {
        "stain": "live/dead fluorescence" if colour else "single channel",
        "coverage_pct": round(100 * total / field, 1),
        "cluster_count": int(cluster_ids.size),
        "micro_colony_count": int(colony_ids.size),
        "largest_cluster_pct": round(100 * largest, 1),
        "clustered_biomass_pct": round(100 * clustered, 1),
        "pattern": pattern,
        "pattern_text": pattern_text,
        "live_pct": round(100 * float(live.sum()) / total, 1) if colour and total else None,
        "matrix_pct": round(100 * float(matrix.mean()), 1) if colour else None,
        "overlay_png": _overlay(img, lab, cluster_ids, colony_ids),
    }
    indicator = {"dense_clusters": 0.8, "micro_colonies": 0.5, "scattered": 0.15}[pattern]
    if pattern == "dense_clusters" and (result["matrix_pct"] or 0) >= 10:
        indicator = 1.0
    result["indicator"] = indicator
    return result


def _overlay(img: Image.Image, lab: np.ndarray, cluster_ids, colony_ids) -> str:
    """Small PNG of the image with clusters (yellow) and micro-colonies (cyan) boxed."""
    view = img.copy()
    view.thumbnail((360, 360))
    sx, sy = view.width / (lab.shape[1] * BLOCK), view.height / (lab.shape[0] * BLOCK)
    draw = ImageDraw.Draw(view)
    for ids, colour in ((colony_ids, (0, 220, 255)), (cluster_ids, (255, 214, 0))):
        for i in ids:
            ys, xs = np.nonzero(lab == i)
            box = (xs.min() * BLOCK * sx, ys.min() * BLOCK * sy, (xs.max() + 1) * BLOCK * sx, (ys.max() + 1) * BLOCK * sy)
            draw.rectangle(box, outline=colour, width=2)
    buf = io.BytesIO()
    view.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ── Raman spectroscopy ───────────────────────────────────────────────────

# Standard Raman band assignments for bacteria (cm^-1).
RAMAN_BANDS = [
    (720, "Adenine (nucleic acids)"),
    (783, "Nucleic acids (DNA/RNA)"),
    (855, "Tyrosine / polysaccharide"),
    (1004, "Phenylalanine (proteins)"),
    (1095, "Polysaccharides, C-O-C (biofilm matrix)"),
    (1125, "Polysaccharides / lipids, C-C"),
    (1250, "Amide III (proteins)"),
    (1335, "Nucleic acids (adenine, guanine)"),
    (1450, "CH2 deformation (lipids, proteins)"),
    (1580, "Nucleic acids (guanine, adenine)"),
    (1660, "Amide I (proteins)"),
]
BAND_TOLERANCE = 15


def _read_spectrum(data: bytes) -> tuple[np.ndarray, np.ndarray]:
    rows = []
    for line in data.decode("utf-8", errors="replace").splitlines():
        parts = line.replace(";", ",").replace("\t", ",").split(",")
        if len(parts) < 2:
            parts = line.split()
        try:
            rows.append((float(parts[0]), float(parts[1])))
        except (ValueError, IndexError):
            continue
    if len(rows) < 20:
        raise ValueError("Spectrum file has too few numeric (wavenumber, intensity) rows.")
    arr = np.array(sorted(rows))
    return arr[:, 0], arr[:, 1]


def _smooth(y: np.ndarray, n: int) -> np.ndarray:
    n = max(3, n | 1)
    return np.convolve(np.pad(y, n // 2, mode="edge"), np.ones(n) / n, mode="valid")[: y.size]


def _baseline(x: np.ndarray, y: np.ndarray, deg: int = 3, iters: int = 30) -> np.ndarray:
    """Iterative polynomial fit that hugs the bottom of the spectrum (fluorescence background)."""
    xs = (x - x.mean()) / (x.std() or 1)
    base = y.copy()
    for _ in range(iters):
        base = np.minimum(base, np.polyval(np.polyfit(xs, base, deg), xs))
    return np.polyval(np.polyfit(xs, base, deg), xs)


def analyze_spectrum(data: bytes) -> dict:
    x, y = _read_spectrum(data)
    step = float(np.median(np.diff(x))) or 1.0
    smooth = _smooth(y, int(round(12 / step)))
    signal = smooth - _baseline(x, smooth)
    height = max(float(signal.max()), 1e-9)
    corr = signal / height
    noise = float(np.std(y - _smooth(y, 5)))
    snr = height / noise if noise > 0 else 999.0

    window = max(1, int(15 / step))
    peaks = [i for i in range(window, x.size - window)
             if corr[i] > 0.15 and corr[i] == corr[i - window: i + window + 1].max()]
    peaks = sorted(sorted(peaks, key=lambda i: -corr[i])[:6])
    peak_list = []
    for i in peaks:
        name = next((n for c, n in RAMAN_BANDS if abs(x[i] - c) <= BAND_TOLERANCE), "Unassigned")
        peak_list.append({"wavenumber": round(float(x[i])), "intensity": round(float(corr[i]), 2), "assignment": name})

    def band_max(lo: float, hi: float) -> float:
        m = (x >= lo) & (x <= hi)
        return float(corr[m].max()) if m.any() else 0.0

    protein = band_max(1640, 1680)
    ratio = band_max(1080, 1150) / protein if protein > 0.05 else None
    if ratio is None:
        level, level_text, indicator = "unknown", "Protein reference band not found; matrix signal not assessed", None
    elif ratio >= 0.9:
        level, level_text, indicator = "strong", "Strong polysaccharide band, consistent with biofilm matrix", 0.85
    elif ratio >= 0.5:
        level, level_text, indicator = "moderate", "Moderate polysaccharide band", 0.5
    else:
        level, level_text, indicator = "weak", "Weak polysaccharide band, little matrix signal", 0.15

    quality = "good" if snr >= 20 else "fair" if snr >= 8 else "poor"
    stride = max(1, x.size // 300)
    return {
        "range_cm": [round(float(x.min())), round(float(x.max()))],
        "points": int(x.size),
        "snr": round(snr, 1),
        "quality": quality,
        "peaks": peak_list,
        "matrix_ratio": round(ratio, 2) if ratio is not None else None,
        "matrix_level": level,
        "matrix_text": level_text,
        "indicator": indicator,
        "trace": [[round(float(a), 1), round(float(b), 3)] for a, b in zip(x[::stride], corr[::stride])],
    }


# ── Genomics ─────────────────────────────────────────────────────────────

KMER = 31
GENE_PRESENT = 0.80            # >= 80% of a gene's 31-mers found in the genome
MARKERS = {
    "mecA": "Methicillin resistance (MRSA / MRSE): resistant to beta-lactam antibiotics",
    "icaA": "Biofilm matrix (PIA) synthesis",
    "icaD": "Biofilm matrix (PIA) synthesis, partner of icaA",
    "icaB": "Biofilm matrix (PIA) modification",
    "icaC": "Biofilm matrix (PIA) export",
}
_CODE = np.full(256, -1, dtype=np.int64)
for _i, _ch in enumerate(b"ACGT"):
    _CODE[_ch] = _i


def _contigs(text: str) -> list[str]:
    from ml.inference.genomic_research_service import parse_fasta
    return parse_fasta(text)


def _kmers(seq: str) -> np.ndarray:
    """Canonical 31-mer codes (forward/reverse-complement minimum), skipping non-ACGT."""
    codes = _CODE[np.frombuffer(seq.encode("ascii"), dtype=np.uint8)]
    if codes.size < KMER:
        return np.zeros(0, dtype=np.int64)
    n = codes.size - KMER + 1
    fwd = np.zeros(n, dtype=np.int64)
    rev = np.zeros(n, dtype=np.int64)
    valid = np.ones(n, dtype=bool)
    for j in range(KMER):
        window = codes[j:j + n]
        valid &= window >= 0
        base = np.maximum(window, 0)
        fwd = fwd * 4 + base
        rev += (3 - base) << (2 * j)
    return np.minimum(fwd, rev)[valid]


def _marker_panel() -> list[tuple[str, str, np.ndarray]]:
    genes, header, seq = [], None, []
    for line in (ARTIFACTS / "marker_genes.fasta").read_text().splitlines():
        if line.startswith("#"):
            continue
        if line.startswith(">"):
            if header:
                genes.append((header, "".join(seq)))
            header, seq = line[1:], []
        elif line.strip():
            seq.append(line.strip())
    if header:
        genes.append((header, "".join(seq)))
    return [(h.split("|")[0], h.split("|")[1], np.unique(_kmers(s))) for h, s in genes]


_PANEL: Optional[list] = None


def screen_markers(contigs: list[str]) -> list[dict]:
    global _PANEL
    if _PANEL is None:
        _PANEL = _marker_panel()
    genome = np.unique(np.concatenate([_kmers(c) for c in contigs]))
    best: dict[str, tuple[float, str]] = {}
    for gene, species, kmers in _PANEL:
        cover = float(np.isin(kmers, genome, assume_unique=True).mean()) if kmers.size else 0.0
        if cover > best.get(gene, (-1.0, ""))[0]:
            best[gene] = (cover, species)
    return [{"gene": g, "role": MARKERS[g], "present": c >= GENE_PRESENT,
             "coverage_pct": round(100 * c, 1), "closest_reference": s}
            for g, (c, s) in best.items()]


def analyze_genome(text: str) -> dict:
    contigs = _contigs(text)
    lengths = sorted((len(c) for c in contigs), reverse=True)
    total = sum(lengths)
    half, running, n50 = total / 2, 0, 0
    for length in lengths:
        running += length
        if running >= half:
            n50 = length
            break
    joined = "".join(contigs)
    gc = (joined.count("G") + joined.count("C")) / max(total, 1)

    markers = screen_markers(contigs) if total >= 10_000 else []
    present = {m["gene"] for m in markers if m["present"]}
    ica = {"icaA", "icaD"} <= present
    result = {
        "length_bp": total,
        "contigs": len(contigs),
        "n50_bp": n50,
        "gc_pct": round(100 * gc, 1),
        "markers": markers,
        "mecA": "mecA" in present,
        "ica_operon": ica,
        "indicator": 0.9 if ica else None,
        "genomic_model": _genomic_model(text),
    }
    return result


def _genomic_model(text: str) -> dict:
    from ml.inference.genomic_research_service import get_service
    service = get_service()
    if not service.is_loaded:
        return {"status": "unavailable", "reasons": ["Genomic model artifact is unavailable."]}
    try:
        return service.predict_from_fasta(text)
    except ValueError as exc:
        return {"status": "unavailable", "reasons": [str(exc)]}


# ── Clinical risk factors ────────────────────────────────────────────────

def analyze_clinical(clinical: dict) -> dict:
    context = clinical.get("infectionContext") or ""
    days = int(clinical.get("chronicityDays") or 0)
    treatment = clinical.get("previousTreatment") or ""
    culture = clinical.get("previousCulture") or ""
    factors = [
        {"factor": "Chronic infection (4 weeks or longer)",
         "present": days >= 28,
         "why": "Biofilm infections persist; most chronic wounds contain biofilm."},
        {"factor": "Implant, catheter or other device",
         "present": bool(clinical.get("implantPresent")) or context in ("orthopedic-implant", "catheter"),
         "why": "Bacteria form biofilm on device surfaces."},
        {"factor": "Infection persisting despite treatment",
         "present": treatment in ("antibiotics", "combination", "surgical-debridement"),
         "why": "Biofilm protects bacteria from antibiotics and the immune system."},
        {"factor": "Chronic wound or device-related setting",
         "present": context in ("chronic-wound", "orthopedic-implant", "catheter"),
         "why": "These are the settings where biofilm infection is most common."},
        {"factor": "Negative or inconclusive culture",
         "present": culture in ("negative", "unknown"),
         "why": "Standard culture often misses bacteria living in biofilm."},
    ]
    count = sum(f["present"] for f in factors)
    return {"factors": factors, "present_count": count, "total": len(factors),
            "indicator": round(count / len(factors), 2)}


# ── Combined evidence score ──────────────────────────────────────────────

LABELS = {"microscopy": "Microscopy", "spectroscopy": "Raman spectroscopy",
          "genomics": "Genomics", "clinical": "Clinical risk factors"}


def combine(evidence: dict) -> tuple[Optional[float], list[dict], list[str]]:
    """
    Equal-weight average of the indicators that could be measured.
    Returns (score or None, contributions, plain-language key findings).
    """
    used = [(k, v["indicator"]) for k, v in evidence.items()
            if isinstance(v, dict) and v.get("indicator") is not None]
    contributions = [{"modality": k, "label": LABELS[k], "indicator": round(i, 2),
                      "weight": round(1 / len(used), 2)} for k, i in used]
    score = round(sum(i for _, i in used) / len(used), 3) if used else None
    return score, contributions, key_findings(evidence)


def key_findings(evidence: dict) -> list[str]:
    """Short plain-language findings, most important first (the UI shows the top few)."""
    main, extra = [], []
    g = evidence.get("genomics")
    if g and "error" not in g:
        if g["mecA"]:
            main.append("Antibiotic-resistance gene mecA found (methicillin resistance, MRSA/MRSE).")
        if g["ica_operon"]:
            main.append("Biofilm-forming genes (ica) found in the genome.")
        if g["markers"] and not g["mecA"] and not g["ica_operon"]:
            extra.append("No resistance or biofilm genes found in the staphylococcal gene panel.")
        model = g.get("genomic_model") or {}
        if model.get("status") == "completed":
            extra.append(f"Trained genomic model: {model['predicted_class']} S. epidermidis "
                         f"({round(100 * model['probability_pathogenic'])}% probability pathogenic).")
    m = evidence.get("microscopy")
    if m and "error" not in m:
        main.append(f"{m['pattern_text']} ({m['clustered_biomass_pct']}% of cells in clusters).")
        if m.get("live_pct") is not None and m["live_pct"] < 60:
            main.append(f"Only {m['live_pct']}% of cells are alive, consistent with antibiotic damage.")
    s = evidence.get("spectroscopy")
    if s and "error" not in s and s["matrix_ratio"] is not None:
        main.append(f"Raman: {s['matrix_text'].lower()}.")
        if s["quality"] == "poor":
            extra.append(f"Raman signal quality is low (signal-to-noise {s['snr']}); interpret with caution.")
    c = evidence.get("clinical")
    if c:
        main.append(f"{c['present_count']} of {c['total']} clinical biofilm risk factors present.")
    return main + extra
