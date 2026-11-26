# BiofilmAI — Viva Preparation

Likely viva questions with concise, honest answers.

---

### Q: What problem does BiofilmAI solve?

**A:** BiofilmAI addresses the lack of a modular, extensible software framework for multimodal biofilm research. Currently, most biofilm analysis tools work with only one data modality (microscopy OR spectroscopy OR genomics). BiofilmAI provides a complete frontend-to-backend platform that can accept all four modalities and combine them through a cross-attention Transformer. It is a research framework, not a clinical diagnostic system.

---

### Q: Why multimodal learning?

**A:** Biofilms are structurally and chemically complex. No single measurement modality captures the full picture. Microscopy shows spatial organization, spectroscopy reveals chemical composition, genomics provides taxonomic and functional information, and clinical metadata gives patient context. Multimodal learning allows the model to build a richer representation by combining these complementary signals.

---

### Q: Why use separate encoders?

**A:** Each modality has fundamentally different data characteristics. Images are 2D spatial grids, spectra are 1D sequences, genomic data is symbolic sequences, and clinical data is structured tabular information. Separate encoders allow each modality to use an appropriate architecture (ViT for images, Transformer for sequences, MLP for tabular data) before projecting into a shared embedding space.

---

### Q: What is cross-attention?

**A:** Cross-attention is a mechanism that allows each modality representation to attend to every other modality representation. In the BiofilmAI fusion transformer, the microscopy embedding can learn which parts of the spectroscopy or genomics embeddings are most relevant. This creates a weighted combination where the model can focus on inter-modal relationships rather than treating all modalities independently.

---

### Q: Why use a Transformer?

**A:** Transformers excel at capturing long-range dependencies and relationships between elements in a sequence. In the fusion context, the "sequence" is the set of four modality embeddings. The Transformer's self-attention and cross-attention mechanisms naturally model the interactions between modalities, which is a core requirement for multimodal fusion.

---

### Q: How are missing modalities handled?

**A:** Missing modalities are supported through modality masks. If a modality is not provided, a zero embedding tensor is passed to the fusion layer, and a boolean mask tells the cross-attention which embeddings are real versus padding. The model can produce a prediction using whatever subset of modalities is available. This design allows the system to work with incomplete data.

---

### Q: What data does the system require?

**A:** The system is designed to accept four modalities per sample: a microscopy image (PNG/JPG/TIFF), a spectroscopy file (CSV/TXT with wavelength and intensity columns), a genomic sequence file (FASTA/CSV/TXT), and structured clinical metadata. Each sample must have a unique `sample_id` that links all its modality files. Missing modalities are allowed.

---

### Q: Why haven't you trained the final model?

**A:** Training requires a labelled multimodal dataset where each sample has all four modalities and a consistent binary biofilm label. Our investigation identified no publicly available dataset that meets these requirements. The model architecture, data loader, and training pipeline are complete and ready, but no suitable training data exists yet. This is honestly documented in the dataset feasibility analysis.

---

### Q: Why can't the three public datasets simply be merged?

**A:** The DeepBacs microscopy dataset, the Ho et al. Raman spectroscopy dataset, and the NCBI 16S genomic dataset are from different laboratories, using different bacterial species, different growth conditions, and different labeling schemes. There is no sample-level correspondence between them — we cannot know which microscopy image goes with which Raman spectrum. Training a cross-attention fusion model requires paired data from the same samples. Merging unrelated datasets would produce scientifically meaningless results.

---

### Q: What does DEMO MODE mean?

**A:** DEMO MODE is a fallback inference mode that activates when no trained model weights are available. Instead of the real PyTorch model, a simple heuristic generates plausible-looking predictions based on how many modalities were uploaded, plus random noise. Every DEMO MODE response is clearly labeled with `demoMode: true`, `modelMode: "demo"`, and a message stating that no clinical prediction is being generated. The demo mode demonstrates the full frontend-to-backend workflow without requiring a trained model.

---

### Q: Is this a medical diagnostic system?

**A:** No. BiofilmAI is a research prototype. It is not a medical device, it has not been clinically validated, it has not been cleared by any regulatory authority, and it must not be used to make clinical decisions. Every page of the application includes a clear disclaimer to this effect.

---

### Q: How was the system tested?

**A:** The system passes an automated end-to-end test suite of 37 tests covering: server health, all 8 frontend pages (HTTP 200), all 4 API endpoints, response structure validation, error handling (missing fields, invalid files, 404s), CORS headers, frontend-backend integration, TypeScript compilation, and the full frontend-to-backend workflow. All 37 tests pass.

---

### Q: What are the limitations?

**A:** The primary limitations are: (1) no trained model weights exist — all predictions are simulated; (2) no real multimodal labelled dataset is available; (3) demo predictions are not scientifically meaningful; (4) the system has not been clinically validated; (5) public single-modality datasets cannot be merged into a multimodal training set; (6) analysis storage is in-memory and non-persistent; (7) there is no user authentication.

---

### Q: What is the future scope?

**A:** The immediate next step is to acquire a paired multimodal dataset through laboratory collection or collaboration. Once data is available, the model can be trained, evaluated, and ablated. Explainability features (real attention maps, Grad-CAM) can be integrated. Finally, the system can be validated on independent data and deployed for real inference.

---

### Q: What is your contribution?

**A:** My contributions are:

1. **A professional biomedical frontend** (Next.js, 8 pages, 6-step analysis wizard, results dashboard, cross-attention visualization) — 37 end-to-end tests verify the complete workflow.

2. **A FastAPI backend** with file validation, input validation, in-memory storage, and a clean API abstraction that can switch between demo and real mode without frontend changes.

3. **A modular PyTorch multimodal Transformer architecture** with four modality-specific encoders, cross-attention fusion, missing-modality handling, and complete training/evaluation/inference pipelines.

4. **A dataset loader and validator** that is built, tested, and ready for real labelled data. The validator checks structure, file existence, class balance, and data leakage.

5. **An honest dataset feasibility analysis** demonstrating that no public multimodal biofilm dataset currently exists, with clear documentation of what data would be required.

6. **Comprehensive documentation** covering architecture, methodology, API, testing, limitations, and future work.

---

*Last updated: August 2026*