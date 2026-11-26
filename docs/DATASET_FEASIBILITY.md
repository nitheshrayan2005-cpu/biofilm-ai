# BiofilmAI — Dataset Feasibility Analysis

## Honest Assessment

**No single publicly available dataset provides all four required modalities (microscopy, spectroscopy, genomics, AND structured clinical metadata) for the same biofilm samples with usable labels.**

This is the central finding of the dataset investigation. It has direct implications for the project.

---

## Datasets Investigated

Eight candidate datasets and repositories were evaluated during this study:

| Dataset | Source | Modalities | Label | Samples | Can Train Multimodal Model |
|---|---|---|---|---|---|
| DeepBacs | Zenodo (CC-BY 4.0) | Microscopy only | Growth stage | ~160 images | No — single modality |
| Ho et al. Raman | RamanSPy / open | Spectroscopy only | Species | 60,000 spectra | No — single modality |
| NCBI PRJNA433427 | NCBI SRA / public | Genomics only (16S) | Environment | 102 samples | No — single modality |
| NASA P. aeruginosa | NASA OSDR / public | Transcriptomics | Formation | ~30 samples | No — two modalities max |
| EPA Biofilm Dataset | EPA Science Hub | Transcriptomics + qPCR | Exposure | ~20 samples | No — two modalities max |
| EWMA Biofilm Library | Univ. Copenhagen | CLSM images only | None (figures) | N/A | No — not a structured dataset |
| Kaggle Biofilm | Kaggle | Unknown | Unknown | Unknown | No — provenance unclear |
| Literature studies | Various | Microscopy + Raman | Experimental | Varies | Not publicly deposited |

## Compatibility Matrix

| Dataset | Microscopy | Spectroscopy | Genomics | Clinical | Biofilm Label | All 4 Modalities |
|---|---|---|---|---|---|---|
| DeepBacs | ✅ | ❌ | ❌ | ❌ | ❌ (growth stage) | ❌ |
| Ho et al. Raman | ❌ | ✅ | ❌ | ❌ | ❌ (species) | ❌ |
| NCBI PRJNA433427 | ❌ | ❌ | ✅ | ❌ | ❌ (all biofilm) | ❌ |
| NASA OSDR | ❌ | ❌ | ✅ (RNA-seq) | ✅ (partial) | Partial | ❌ |
| EPA Biofilm | ❌ | ❌ | ✅ (RNA-seq) | ❌ | ❌ (exposure) | ❌ |

**No dataset achieves all five columns.** Every candidate is missing at least two to three modalities.

## Category Classification

### Category A: Genuinely Multimodal with Linked Sample IDs

**None found.** No public dataset provides even three modalities from the same samples.

### Category B: Useful for Modality-Specific Pretraining

| Dataset | Can Pretrain |
|---|---|
| DeepBacs | Vision Encoder |
| Ho et al. Raman | Spectral Encoder |
| NCBI SRA PRJNA433427 | Genomic Encoder |

These datasets use **different samples, different organisms, and different labeling schemas**. They cannot be merged into a single multimodal training set because sample-level cross-modal correspondence does not exist.

### Category C: Unsuitable

- **Kaggle "Biofilm"** — provenance unclear, single image only, no multimodal content
- **EWMA Library** — not a structured downloadable dataset

## Why Separate Datasets Cannot Be Merged

It may be tempting to combine, for example:

- Microscopy images from DeepBacs
- Raman spectra from Ho et al.
- Genomic data from NCBI SRA

into a single "multimodal" training set. This is scientifically invalid for multimodal supervised learning because:

1. **No sample correspondence.** There is no way to know which microscopy image corresponds to which Raman spectrum or which genomic sample. The model requires paired data — all modalities from the same biological sample.

2. **Different biological sources.** DeepBacs uses laboratory strains (*E. coli*, *S. aureus*). The Raman dataset uses clinical isolates from ATCC. The genomic dataset uses environmental drinking water samples. These are fundamentally different populations.

3. **Different labeling schemes.** One dataset has growth stages, another has species labels, another has no labels. There is no consistent biofilm definition.

4. **Alignment is impossible without paired metadata.** Cross-modal embedding alignment requires known correspondences. Random pairing would destroy any meaningful relationship.

## Recommendation

The project should be presented as:

> **"A modular multimodal framework for biofilm research — ready for future data"**

rather than:

> "A trained biofilm detection system"

This is **scientifically honest** and **defensible in an academic project**. The framework is complete and functional. Only paired multimodal data is missing, and its absence is clearly documented.

## What Would Be Required

To train the model, a researcher needs to collect:

1. 50–100+ biofilm samples
2. For each sample: microscopy image, spectroscopy measurement, genomic sequencing, and structured clinical metadata
3. A consistent binary biofilm label
4. Identical sample IDs across all four modalities

This is feasible in a laboratory setting with access to imaging, spectroscopy, and sequencing equipment — but no such dataset is currently publicly available.

---

*Last updated: August 2026*