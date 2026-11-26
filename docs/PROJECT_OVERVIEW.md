# BiofilmAI — A Modular Multimodal Framework for Biofilm Research

## Problem Statement

Biofilm-associated infections are a major challenge in clinical and research settings. Biofilms are spatially organized, structurally heterogeneous communities of microorganisms embedded in a self-produced extracellular matrix. Their complex biology involves chemical, structural, and molecular dimensions that are difficult to capture with any single measurement modality.

Current approaches to biofilm analysis typically rely on one modality — microscopy, spectroscopy, or genomics — and miss the complementary information that other modalities provide. There is no widely available framework that integrates multiple evidence streams into a unified computational representation for research-oriented biofilm assessment.

## Motivation

The motivation for BiofilmAI is to explore whether fusing complementary data modalities through a cross-attention Transformer can produce a richer, more evidence-aware computational representation of biofilm samples. By building a modular, extensible framework, we enable future researchers to:

1. Integrate existing single-modality datasets into a multimodal pipeline
2. Train and evaluate cross-modal models when paired data becomes available
3. Leverage modern Transformer architectures for biofilm research
4. Maintain transparency, reproducibility, and scientific honesty throughout

## Objectives

| Objective | Status |
|---|---|
| Build a professional biomedical frontend for multimodal sample submission | ✅ Complete |
| Create a FastAPI backend that accepts microscopy, spectroscopy, genomic, and clinical data | ✅ Complete |
| Design a modular PyTorch multimodal Transformer architecture | ✅ Complete |
| Implement per-modality encoders with cross-attention fusion | ✅ Complete |
| Support missing modalities via mask-based handling | ✅ Complete |
| Build a dataset loader and validator for future labelled data | ✅ Complete |
| Document the dataset feasibility analysis honestly | ✅ Complete |
| Provide 37 end-to-end tests that verify the complete pipeline | ✅ Complete |
| Train a real multimodal model on a labelled dataset | ❌ Not yet — no suitable public dataset exists |

## Proposed Solution

BiofilmAI is a modular research framework with these components:

1. **Frontend Application** — A Next.js/React web app where researchers can upload sample data across four modalities: microscopy images, spectroscopy files, genomic sequences, and structured clinical metadata. The frontend presents analysis results through a professional analytics dashboard with risk visualization, modality evidence cards, and cross-attention interpretation matrices.

2. **FastAPI Backend** — A Python API server that accepts uploads, validates inputs, and routes requests through either the demo inference engine or the real PyTorch model (if trained weights are provided).

3. **Multimodal Transformer Model** — A PyTorch architecture with four modality-specific encoders (Vision Transformer for microscopy, 1D Transformer for spectroscopy, Transformer for genomics, MLP for clinical data) whose outputs are fused via a cross-attention fusion Transformer into a unified representation for biofilm risk prediction.

4. **Dataset Infrastructure** — A data loader and validator that enforces consistent formatting and can load a real labelled dataset when one becomes available.

## Scope

The project scope includes:
- A complete frontend-backend application workflow
- A modular PyTorch model architecture ready for training
- A dataset loader and validator
- 37 end-to-end tests
- Honest documentation of the data limitations

The following are **out of scope**:
- Clinical validation or deployment
- A trained model with proven accuracy
- A real labelled multimodal dataset
- Claims of clinical diagnostic ability

## Research Prototype Status

**BiofilmAI is a research prototype.** It is not a clinical diagnostic system. The system runs in **DEMO MODE** by default, generating clearly labeled simulated predictions. No real clinical or scientific prediction is made until (a) a real labelled multimodal dataset is provided, (b) the model is trained, and (c) the environment variable is set to disable demo mode.

The existing frontend, backend, and model architecture serve as a complete, extensible framework that is ready for future data integration.

---
*Last updated: August 2026*