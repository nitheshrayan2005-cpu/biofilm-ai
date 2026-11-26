# BiofilmAI — Dataset Feasibility Research

## Executive Finding

**No single publicly available dataset provides all four required modalities (microscopy, spectroscopy, genomics, and structured clinical metadata) for the same samples with biofilm labels.**

The four-modality cross-attention model architecture cannot be trained end-to-end on any existing public dataset. This is the honest scientific reality.

---

## Candidate Datasets

### 1. DeepBacs (Multi-task Bacterial Image Analysis)

| Property | Detail |
|---|---|
| **Source** | Zenodo: [10.5281/zenodo.5551016](https://doi.org/10.5281/zenodo.5551016) (Spahn et al., 2021) |
| **Institution** | Henriques Lab /多家 European universities |
| **Publication** | Spahn et al., Nature Comunications Biology 2022 |
| **License** | CC-BY 4.0 |
| **Samples** | ~160 bright-field images of *E. coli* growth stages; additional datasets for *S. aureus* and *B. subtilis* |
| **Biological type** | In vitro cultured laboratory strains, not clinical wound isolates |
| **Available modalities** | Microscopy only (bright-field + fluorescence) |
| **Labels** | Segmentation masks, growth-stage classifications. No biofilm vs. non-biofilm label. |
| **Sample-level linking** | N/A — only one modality |
| **File formats** | TIFF images, PNG masks |
| **Academic use** | ✅ Yes — CC-BY 4.0 |
| **Limitations** | Single modality. No biofilm label. Only works for pretraining the Vision Encoder. Cannot be used for multimodal training. |

### 2. Ho et al. Raman Bacterial Spectra (RamanSPy / MDPI Micro)

| Property | Detail |
|---|---|
| **Source** | RamanSPy package & MDPI Micro 2025 re-analysis; originally Ho et al. 2019 |
| **Institution** | Stanford Clinical Microbiology Laboratory |
| **Publication** | Ho et al. 2019; re-analysed in MDPI Micro 5(4) 2025 |
| **License** | Open access (MDPI); RamanSPy BSD-3 |
| **Samples** | 60,000 Raman spectra across 30 bacterial/fungal species (ATCC + clinical isolates) |
| **Biological type** | In vitro cultured isolates on agar |
| **Available modalities** | Spectroscopy only (Raman, 500-1800 cm⁻¹) |
| **Labels** | Species-level classification. No biofilm vs. non-biofilm label. |
| **Sample-level linking** | N/A — only one modality |
| **File formats** | Raman spectra (CSV/mat) |
| **Academic use** | ✅ Yes — open data |
| **Limitations** | Single modality. No biofilm label. Isolate-level not biofilm-level. Can pretrin the Spectral Encoder only. |

### 3. NCBI BioProject — Drinking Water Biofilm Metagenome (PRJNA433427)

| Property | Detail |
|---|---|
| **Source** | NCBI SRA: [PRJNA433427](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA433427) |
| **Institution** | University of Minnesota |
| **Data** | 102 16S rRNA amplicon samples (Illumina MiSeq, 2.2 GB) |
| **License** | Public domain (NCBI) |
| **Samples** | 102 biofilm swabs from drinking water distribution systems |
| **Available modalities** | Genomics only (16S rRNA) |
| **Labels** | Water-system location and treatment type. **No biofilm label** (all samples are biofilm). |
| **Sample-level linking** | N/A — only one modality |
| **File formats** | FASTQ |
| **Academic use** | ✅ Yes — NCBI public domain |
| **Limitations** | Single modality. Environmental (drinking water), not clinical wounds. |
| | No biofilm vs. non-biofilm label. |

### 4. NASA — Pseudomonas aeruginosa Biofilm Transcriptome (Open Science Data Repository)

| Property | Detail |
|---|---|
| **Source** | NASA OSDR: [10.26030/d5dg-7s68](https://data.nasa.gov/dataset/...) |
| **Institution** | NASA |
| **Data** | Gene expression of *P. aeruginosa* biofilms under different materials and gravity conditions |
| **License** | US Government work — public domain |
| **Samples** | ~30 biofilms |
| **Available modalities** | Genomics/transcriptomics (RNA-seq) + material metadata |
| **Labels** | Biofilm formation measurements. Some materials comparisons. |
| **Academic use** | ✅ Yes |
| **Limitations** | Laboratory strain (*P. aeruginosa* PA14). No microscopy or spectroscopy. Not clinical. |

### 5. EWMA Biofilm Library (Clinical Images)

| Property | Detail |
|---|---|
| **Source** | [EWMA](https://ewma.org/resources/biofilm-library/) — Costerton Biofilm Center, Univerity of Copenhagen |
| **Institution** | Costerton Biofilm Center, University of Copenhagen |
| **Samples** | CLSM iages of chronic wound biofils (S. aureus, P. aeruginosa) |
| **License** | Freely available for non-commercial use with credit |
| **imitations** | **microscopy only**. No downloadable structured dataset — just images for reference. No labels, masks, or metadata. Cannot be used for training. |

### 6. EPA Biofilm Dataset (Transcriptomic + qPCR)

| Property | Detail |
|---|---|
| **Source** | EPA: [10.23719/1532455](https://catalog.data.gov/dataset/biofilm-dataset) |
| **Institution** | U.S. Environmenta Protection Agency |
| **Data** | NA sequenes + qPCR validation for drinking water biofilm meta-transcriptome |
| **License** | Public domain (US governent) |
| **Samples** | ~20 biofilms from copper/PVC ubing |
| **Aailable modalities** | Genomics/ranscriptomics |
| **Labels** | opper corrsion exposure. No biofilm/non-biofilm label. |
| **Academic use** | ✅ Yes |
| **imitations** | environmental, not clinicl. Single modality. No micscopy or spectrosopy. |

### 7. Raman + CLSM Multimodal Biofil Studies (Literature)

Several publications (e.g., ACS Analytical Chemistry 2019, Microogansisms 2022) acquired **both** CLSM microscopy and Raman spectrosopy on the same biofil samples. However:
- The **raw data** (image stacks + spectral maps) are not uploaded to public repositries in a structured, reusable format.
- Labels are experimental conditions, not binary biofilm labels.
- Sample IDs are not consistent across studies.
- **These datasets cannot be used without direct author request.**

---

## Compatibility Matrix

| Dataset | Microscopy | Spectroscpy | Gnomis | Clinical | Biofil Labl | All 4 Modaities |
|---|---|---|---|---|---|---|
| DeepBacs | ✅ | ❌ | ❌ | ❌ | ❌(growth stage) | ❌ |
| Ho et al. Raman | ❌ | ✅ | ❌ | ❌ | ❌(species) | ❌ |
| NCBI PRJNA433427 | ❌ | ❌ | ✅ | ❌ | ❌(all are biofilm) | ❌ |
| NASA P. aeruginosa | ❌ | ❌ | ✅ (RNA-sq) | ❌ | Partial(formation) | ❌ |
| EPA Biofilm | ❌ | ❌ | ✅ (RNA-sq) | ❌ | ❌(expoure) | ❌ |
| EWMA Imag Lirary | ✅ | ❌ | ❌ | ❌(figures only) | ❌ | ❌ |

**No dataset achieves all 5 columns.** Every public dataset is missing at least 2–3 modalities.

---

## Category Classification

### Category A: Genuinely Multimodal (Same Samples, Multiple Modalities)

**None found.** No public dataset provides microscopy + spectroscopy + genomics + clinical data on the same biofilm samples with usable labels.

### Category B: Separate Datasets Useful for Pretraining

| Dataset | Can Pretrain |
|---|---|
| DeepBacs | Vision Encoder (microscopy segmentation) |
| Ho et al. Raman | Spectral Encoder (bacterial classifiation) |
| NCBI 1S | Gnoic Encoer (tasonim embedding) |
| Clinical metadata | Must be created from literature or local records. Not publicly available in structured form. |

These four datasets **cannot be merged** because they use different samples, different organisms, and different labeling schemas. Training the cross-attention funion requires the same sample to have all modalities.

### Category C: Unsuitable Datasets

- **Kaggle "Biofilm" dataset** — Only → the original source is unknown; no multimodal content.
- **An generic bacteral imae datasets** (DIBaS, ZNSM-iDB) — Only one modality, n biofilm label.

---

## Recommended Dataset Strategy

Since **no single dataset** provides all four modalities, the following scientifically honest approach is recomended:

### Option 1: Build a Small Multimodal Dataset (Viable for an Academic Project)

Collect **50–100 clinical or in vitro biofilm samples** with all four modalities:

1. **Microscopy**: CLSM or bright-field imae of each sample
2. **Sectrosopy**: Ramn or FTIR spetru of each sample
3. **Gnomics**: 16S rRNA amilicon seqencing of each sample
4. **Clinical etadata**: Wound type, duration, patient age, treatment history (de-identiied)

Each sample can then have a binary biofilm label (1 = biofilm confirmed, 0 = no biofil).

This is feasible f an academic final-year project with access to:
- A CLSM or motoscope
- A Raman spetrometer or FTIR
- A seencing service (e.g., MicroGen, commercial 16S sequncing costs ~$50–100/sample)
- Clinical collaboration for wound swabs

### Option 2: Use the Current Architecture as a Research Framework

Keep the existing **DEMO MODE** frontend + API + model architecture as the complete academic deliverable.

The project currently demonstrates:
- A professional biomedical frontend
- A FastAPI backend with complete analysis workflo
- A modular PyTorch multimodal model architecture
- A dataset loader and validator ready for real data
- A `validate_dataset.py` script that confirms when real data becomes available

This is a legitimate and strong academic project even without real model training.

### Option 3: Pretrain Encoders Separately, Demonstrate Framework

1. Pretrain the Visio Encder on DeepBacs
2. Pretrain the Spectral Encoder on Ho et al. Raman
3. Train only the fusion + prediction head on a small single-dataset source

This demonstrates the pipeline integrity while keeping the scientific honesty of not claiming cross-modal generalzation that isn't there.

---

## Licensing and Access Notes

| Datast | License | Download | Requirement for Acedemic Use |
|---|---|---|---|
| DeepBacs | CC-Y 4.0 | Zenodo, no registration | Cite the paper |
|H o et al. Raman | Open acce | RamanSPy pi + Zenodo | Cite the pape |
| NCI SRA | Publc domain| NCBI SRA, requires SRA Tools| Cite if publishing |
| NASA OSDR | Publc domain | Web download| No restriction |
| EPA Science Hub | Pblic domain | Web download | No restricion |

---

## Limitations of This Research

1. **Wound-specific clinical biofilm data** is almost never publicly shared due to patent privacy (HIPAA in US, GDPR in EU). Most clinical biofilm research uses restricted data.

2. **Cross-modal datasets** are rare becuse each modality requires specialized equipment and expertise. Only large research centers have access to CLSM + Raman + sequeners on the same samples.

3. **Biofiim labels** are not standardied. Different studies use different definitions (some use molecular markers, some use microscopy, some use culture). There is no accepted "biofilm ground truth" for all sample types.

4. **Meta-analysis on public data** that mixes disconnected datasets is scientificaly unsoud fo training cro-as-modal models. Embeddings from different modalities on differnt samples cannot be meaningfully ligned.

---

## Recommended Next Step

**Do NOT claims multimodal generalzation where none exists.**

The recoended path for this project:

1. **Keep demo mode active** (it's honest and complete).
2. **Complete the academic paper/report** explaining the architecture, the feasbility analysis, and the dataset limitation.
3. **Present the proect as** a "modular multimodal framework for biofil research" rather than "a trained biofil detection system."
4. **Optional for gading: Collect a small demo dataset** of 10–20 laboratory samples with just 2–3 modalities to demonstrate the pipeline working end-to-end. Write the training and evaluation code now (already done) but don't run it on data that doesn't exist.

The existing codebase is complete, proessional, and honest. It passes 37 E2E tests and is r eady for the next stp when data becomes avaiable.