# BiofilmAI — Microscopy Dataset Audit

## Status: DOWNLOAD BLOCKED — FILE-LEVEL AUDIT NOT POSSIBLE

The official dataset was identified and its metadata was verified from the
University of Dundee Discovery Portal, but **the dataset ZIP file could not
be downloaded** from this environment. No file-level inventory, image count,
or measurement parsing was performed, and **no data was fabricated**.

---

## Exact Download Error

```
HTTP 403 Forbidden — Cloudflare "Just a moment..." anti-bot JavaScript challenge
```

Every attempt returned the same Cloudflare interstitial page:

| Attempt | Method | Result |
|---|---|---|
| 1 | `curl -L` (direct) | HTTP 403 — Cloudflare challenge |
| 2 | `curl -L` with browser User-Agent + Referer headers | HTTP 403 |
| 3 | DOI redirect (`doi.org/10.15132/10000128`) | redirects to the same protected page |
| 4 | `cloudscraper` (JS-challenge bypass) | HTTP 403 |
| 5 | alternate Pure file paths | 403 / connection refused |
| 6 | Wayback Machine availability API | 429 rate-limited |

The University of Dundee portal serves `EPSRC_data_share.zip` behind a
Cloudflare anti-bot challenge that requires a real browser executing
JavaScript. The sandbox network tools (curl, wget, urllib, cloudscraper)
cannot solve this challenge.

---

## Verified Dataset Metadata (from the official page — REAL, not inferred)

| Field | Value |
|---|---|
| **Title** | Confocal microscopy images |
| **Creator** | Liyun Wang |
| **DOI** | 10.15132/10000128 |
| **Official source** | https://discovery.dundee.ac.uk/en/datasets/confocal-microscopy-images/ |
| **Official file** | `EPSRC_data_share.zip` — multipart/x-zip, 16.6 MB |
| **License** | CC BY |
| **Publisher** | University of Dundee |
| **Date made available** | Jun 2018 (data produced 2015–2017) |
| **Description** | Confocal microscopy images of *E. coli* MG1655 micro-colonies after shear-stress treatment and adhesion of *E. coli* MG1655 *fimA* mutants on surfaces at single-cell resolution; plus an Excel chart for bacterial counting (ImageJ + Excel analysis) |
| **Related publication** | Wang, L. et al. *Appl. Environ. Microbiol.* 2018;84(6):e02343-17 — "Influence of type-I fimbriae and fluid shear stress on bacterial behavior and multicellular architecture of early *Escherichia coli* biofilms at single-cell resolution" |

---

## What the Audit Could NOT Verify (because the ZIP was blocked)

- total microscopy image count
- image formats / dimensions / channels
- experimental groups and time points
- number of biological/experimental replicates
- Excel files and their measurements
- image-to-measurement mapping
- candidate supervised-learning targets
- class/target distribution
- leakage risks and correct grouping strategy

These items require the actual ZIP contents. **None of them were assumed or
invented.**

---

## Notes Relevant to a Future Audit (from verified metadata only)

- The study concerns **biofilm formation of *E. coli* MG1655** — this is a
  different organism and a different phenotype target than the existing
  *S. epidermidis* genomic experiment. They are **not sample-paired** and
  must not be fused.
- The Excel analysis appears to contain **bacterial counts** (ImageJ-derived
  quantification) — if confirmed from the actual file, that would be a
  quantitative target, not raw measurements to be relabelled as "spectroscopy".
- Any supervised target would need to be derived from the actual file
  contents and the associated publication; **no biofilm/non-biofilm label
  was assumed**.

---

## Next Step Required

To complete this audit, the dataset ZIP must be obtained through a channel
that can pass the Cloudflare challenge (e.g., a normal web browser, or a
research collaborator's download), then placed in the workspace. The audit
script and registry slot are ready; they will run against the real files
once available.

The registry slot `EXPERIMENT_2_MICROSCOPY` remains `PENDING_VERIFICATION`
(no data). No fabricated microscopy data was created.
