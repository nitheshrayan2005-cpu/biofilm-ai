# BiofilmAI — End-to-end test data

All files here are **synthetic**. They exercise the pipeline; they are not real patient or lab data.

| File | Use |
|---|---|
| `microscopy_biofilm.png` | Microscopy upload (512×512 fluorescence-style biofilm image) |
| `spectroscopy_raman.csv` | Spectroscopy upload (Raman spectrum, 400–1800 cm⁻¹) |
| `genomics_isolate.fasta` | Genomics upload (3 contigs, ~32% GC like *S. epidermidis*) |
| `genomic_predict_request.json` | Body for `POST /api/research/genomic-predict` (343 features = training-set mean) |
| `thickness_requests.json` | Bodies for `POST /api/research/biofilm-thickness-predict` |
| `invalid_microscopy.pdf` | Wrong file type, should be rejected with 400 |

Regenerate with `.venv\Scripts\python.exe test_data\generate_test_data.py`.

## Automated API test

With the backend running:

```powershell
.venv\Scripts\python.exe test_data\run_e2e_test.py                        # http://localhost:8000
.venv\Scripts\python.exe test_data\run_e2e_test.py http://localhost:8001  # other port
```

## Manual UI test (http://localhost:3000/analyze)

**Step 1 — Sample info**

| Field | Value |
|---|---|
| Sample ID | `S-TEST-001` |
| Study ID | `BF-E2E-2026` |
| Sample Type | Implant sonicate |
| Collection date | 2026-10-15 |
| Infection context | Orthopedic implant |
| Wound / implant context | `Knee prosthesis` |

**Step 2 — Microscopy:** upload `microscopy_biofilm.png`
**Step 3 — Spectroscopy:** upload `spectroscopy_raman.csv` (a spectrum preview should appear)
**Step 4 — Genomics:** upload `genomics_isolate.fasta` (format shows FASTA)

**Step 5 — Clinical**

| Field | Value |
|---|---|
| Infection context | Orthopedic implant |
| Chronicity (days) | `120` |
| Implant present | Yes |
| Sample site | Knee (prosthetic) |
| Previous treatment | Antibiotics |
| Previous culture | Positive (pure) |

Run the analysis and check that:
- the results page shows a probability, a risk category and a **DEMO MODE** banner
- the PDF report downloads
- the analysis appears under **History**

Error cases: try uploading `invalid_microscopy.pdf` as microscopy, or leave Study ID empty. Both should show an error.

## Research endpoints (Swagger)

Open http://localhost:8000/docs and paste `genomic_predict_request.json`, or one entry from
`thickness_requests.json`, into the matching endpoint. The UI does not expose these endpoints.
