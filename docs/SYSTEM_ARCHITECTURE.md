# BiofilmAI — System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Next.js)                        │
│  Landing │ Dashboard │ Analyze │ Results │ History │ Settings   │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP / REST API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend (port 8000)                  │
│                                                                  │
│  POST /api/analyze    │  GET /api/history                       │
│  GET /api/analysis/   │  GET /api/health                       │
│     {id}                                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────────┐   │
│  │ Request  │───▶│   Data       │───▶│  Model Manager       │   │
│  │ Parsing  │    │  Validation  │    │  (demo or real)      │   │
│  └──────────┘    └──────────────┘    └──────────┬───────────┘   │
│                                                 │               │
│                   ┌─────────────────────────────┘               │
│                   ▼                                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                 Modality Preprocessing                    │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │   │
│  │  │Microscopy│  │Spectro-  │  │ Genomics │  │Clinical │  │   │
│  │  │(224×224 │  │scopy     │  │(2048 bp) │  │(32 feat)│  │   │
│  │  │ RGB)    │  │(1024×2)  │  │          │  │         │  │   │
│  │  └────┬────┘  └────┬────┘  └────┬─────┘  └────┬────┘  │   │
│  └───────┼────────────┼────────────┼──────────────┼──────┘   │
│          ▼            ▼            ▼              ▼           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Modality Encoders (PyTorch)                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐  │   │
│  │  │  Vision   │  │ Spectral │  │ Genomic  │  │Clinical │  │   │
│  │  │  Encoder  │  │ Encoder  │  │ Encoder  │  │ Encoder │  │   │
│  │  │  (ViT)    │  │  (1D Tr) │  │  (Tr.)   │  │  (MLP)  │  │   │
│  │  └────┬────┘  └────┬────┘  └────┬─────┘  └────┬────┘  │   │
│  └───────┼────────────┼────────────┼──────────────┼──────┘   │
│          └────────────┼────────────┼──────────────┘           │
│                       ▼            ▼                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Cross-Attention Fusion Transformer            │   │
│  │   4 layers · 8 heads · 256-dim hidden                    │   │
│  │   Each modality attends to every other modality           │   │
│  │   Missing modalities handled via modality masks           │   │
│  └─────────────────────────────┬─────────────────────────┘   │   │
│                               ▼                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Risk Prediction Head (MLP)                      │    │
│  │         2 layers · 128-dim → 1-dim · Sigmoid          │   │
│  └──────────────────────────────┬─────────────────────────┘   │
│                                 ▼                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               Interpretation                            │   │
│  │  · Cross-attention matrix                    │   │
│  │  · per-modality contribution scores                     │   │
│  │  · Demo attention overlay (visual)                     │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└───────────────────────────────────└──────────────────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────────────────┐
                    │        Storage (in-memory)              │
                    │        /api/history                    │
                    └──────────────────────────────────────────┘
```

## Component Descriptions

### 1. Frontend (Next.js / React / TypeScript)

The frontend is a professional biomedical web application serving eight routes:

| Route | Purpose |
|---|---|
| `/` | Landing page with four-modality hero visualization |
| `/dashboard` | Overview metrics, chart, recent analysis table |
| `/analyze` | 6-step wizard (Sample → Microscopy → Spectroscopy → Genomics → Clinical → Review) |
| `/results` | Predition daboard with risk gauge, modality evidence, attention matrix |
| `/history` | Filterable table of all analyses |
| `/reearch` | Architecture docmentation, mode comparison, ablation study |
| `/about` | Project background, timline, team |
| `/settings` | Proile, notifiations, appearance, data preferences |

The frontend communicates with the backend via `lib/api.ts`, a service abstraction layer. When `BACKEND_READY=true`, it sends HTTP requests to the FastAPI server. Othrwise it falls back to mock data.

### 2. FastAPI Backend

The backend is a Python FastAPI server with four CORS-enabled endpoints:

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Services tatus, version, demo mode flag |
| `/api/analyze` | POST | Run a multimodal analysis (multipart form) |
| `/api/history` | GET | List all analyses (newest first) |
| `/api/analysis/{id}` | GET | Retrieve a single analysis by ID|

### 3. Model Manager

The `ml_manager.py` module ats as the gateway betwen the API and the ML pipeline:

1. On startup, it looks for tained weights at the onfigured path.
2. If weights exist, it loads the real model.
3. If no weights exist, it reports demo mode.
4. During inference, it calls eith the real model or falls back to demo.

### 4. Dem Inference Engine

When no tained model is avaiable, `service.py` provides a simple heuristic:
- Probability = 0.3 + 0.12(if microscopy) + 0.10(if spectroscopy) + 0.08(if genomics) + 0.10(if clinical) + Gaussian noise
- Risk category = low (<0.4), intermediate (0.4–0.7), high (>0.7)
- Cross-attention = random matrix with diagonal bias
- All outputs clearly marked with `demo_mode=True`

---

*Last updated: August 2026*