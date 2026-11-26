# BiofilmAI — Dataset Expansion Audit

**Date:** August 2026
**Dataset:** S. epidermidis study (103 isolates, Dryad)

## Summary

**NO ADDITIONAL PAIRED MODALITY (raw measurement) AVAILABLE IN CURRENT DATASET**

The only sample-level paired data beyond the genome-derived features is the
**clinical / sample metadata**, which is already imported and matched
103/103 with the genomes. There is **no raw microscopy, no spectroscopy,
and no biofilm phenotype/morphology measurement** anywhere in the project.

## Files Audited

| File | Samples | ID column | Content | Paired with genomes? |
|---|---|---|---|---|
| `BiofilmAI_genomic_features.csv` | 103 | `Identifier` | 343 genomic features (340 k-mer + length + GC + N) | — (source of the genomic experiment) |
| `Dryad_data_metadata (1).csv` | 103 | `Identifier` | Strain, country, year, sequence type, group, Epidemiology, isolation source | ✅ 103/103 exact matches |
| `Dryad+data (1).pdf` | 103 | `Identifier` | Same metadata table (documentation) | ✅ 103/103 |
| `dataset/isolate_metadata.csv` | 103 | `Identifier` | Imported metadata (superset with `label`, `genome_file`) | ✅ 103/103 |

## Modality-by-Modality Findings

### 1. Microscopy / confocal microscopy
**NOT PRESENT.** No raw microscopy image files exist in the project. The only
`.png` files are evaluation figures (ROC, confusion matrix, etc.) generated
from model predictions — these are derived outputs, not raw microscopy.

### 2. Spectroscopy / spectral measurements
**NOT PRESENT.** No Raman, FTIR, or any spectral measurement file exists.
The 340 k-mer features are **genomic-derived composition features**, not
spectroscopy, and must not be described as such.

### 3. Clinical / sample metadata
**PRESENT (the only real paired extra modality).** 103 rows, `Identifier`
column, 103/103 exact sample-level match with the genomes. Columns are all
categorical/identifier fields (country, year, sequence type, group,
Epidemiology, isolation source). No quantitative clinical measurements.

### 4. Biofilm phenotype / morphology measurements
**NOT PRESENT.** The fields `Epidemiology` (pathogenic/commensal) and
`Other isolation information` (source: Prosthetic Joint / Catheter / Skin /
Nasal / Animal) are **categorical labels and sample context**, not phenotype
measurements (no biovolume, thickness, roughness, EPS, CFU, etc.).

## Legitimate Integration of the Clinical Metadata

The clinical metadata IS genuinely paired and could legitimately feed the
**Clinical Encoder** of the future multimodal model:

- 103/103 sample-level match (no missing)
- Integration path already scaffolded: `dataset/isolate_metadata.csv` +
  `splits.json` define isolate-level splits; the `models/clinical_encoder.py`
  interface accepts a 32-dim encoded clinical vector
- It must NOT be relabelled as "raw microscopy" or "spectroscopy"

## Next Research Options (evaluated, NOT implemented)

| Option | Feasibility | Scientific defensibility |
|---|---|---|
| A. Find public paired microscopy + genomics dataset | Low (none found in prior survey) | Medium if found and truly paired |
| B. Find paired spectroscopy + genomics dataset | Low (rare) | Medium if found and truly paired |
| C. **Continue validated genomic experiment; keep multimodal model as architectural contribution** | High | **Highest — fully honest, no fabrication** |
| D. Separate modality-specific experiments (no claimed fusion) | Medium | High IF separate real datasets are obtained and kept separate |

## Recommendation

**Option C.** The genomic experiment is validated on real data with a
leakage-safe protocol and honest metrics. The four-modality architecture is
a genuine, documented research contribution that is explicitly untrained.
Option C requires no fabricated pairing and presents the project truthfully
for a final-year thesis. Options A/B/D require obtaining additional real
datasets before any multimodal claim could be made.
