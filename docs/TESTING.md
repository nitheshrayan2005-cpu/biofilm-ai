# BiofilmAI — Testing

## End-to-End Test Suite

A comprehensive end-to-end test suite validates the complete frontend-to-backend pipeline. The test script is located at `/home/user/e2e_test.sh`.

**Current result: 37 tests passed, 0 tests failed.**

---

## Test Categories

### 1. Service Tests (9 tests)

Verify that both the frontend and backend servers are running and responding.

| Test | What It Checks |
|---|---|
| Backend health | `GET /api/health` returns status=ok |
| Frontend landing page | `/` returns HTTP 200 |
| Frontend dashboard | `/dashboard` returns HTTP 200 |
| Frontend analyze page | `/analyze` returns HTTP 200 |
| Frontend results page | `/results` returns HTTP 200 |
| Frontend history page | `/history` returns HTTP 200 |
| Frontend research page | `/research` returns HTTP 200 |
| Frontend about page | `/about` returns HTTP 200 |
| Frontend settings page | `/settings` returns HTTP 200 |

### 2. API Tests (12 tests)

Verify that every backend endpoint returns the correct response structure.

| Test | What It Checks |
|---|---|
| `GET /api/health` | Status, version, demo mode |
| `POST /api/analyze` (minimal) | Returns completed status + demoMode |
| Analysis ID generation | Unique ID is generated (e.g., BA-XXXXXXXXXXXX) |
| `POST /api/analyze` (4 modalities) | All 4 modality entries in response |
| `GET /api/history` | Returns >= 2 analyses |
| `GET /api/analysis/{id}` | Returns status=completed |
| Response structure | Has all required fields |
| Prediction validation | Probability is 0-1, risk category is low/intermediate/high |
| demoMode | Is `true` |
| modelMode | Is `"demo"` |
| message | Contains "DEMO MODE" |
| crossAttention | CrossAttentionMap is present |

### 3. Error Handling Tests (3 tests)

| Test | What It Checks |
|---|---|
| Missing required field | `POST /api/analyze` with empty input returns 400 with `error: true` |
| Invalid file type | `POST /api/analyze` with `.pdf` labeled as microscopy returns 400 |
| Non-existent analysis ID | `GET /api/analysis/NONEXISTENT` returns 404 with `detail` |

### 4. CORS Test (1 test)

| Test | What It Checks |
|---|---|
| CORS headers | OPTIONS request to `/api/analyze` with origin `http://localhost:3000` returns `access-control-allow-origin` |

### 5. Frontend Code Checks (9 tests)

Verify that the frontend code is correctly connected to the backend.

| Test | What It Checks |
|---|---|
| Frontend API config | `BACKEND_READY = true`, `BACKEND_URL` defined |
| Analyze page imports | Imports `analyze` function and uses `sessionStorage` |
| Results page | Reads `sessionStorage` and displays DEMO MODE badge |
| Results page modelMode | Displays `modelMode` from the API response |
| Dashboard | Fetches history from backend API |
| History page | Fetches from backend API |
| Analyze page | Has `ProcessingOverlay` component |
| TypeScript types | `modelMode` and `message` fields defined |

### 6. TypeScript Compilation (1 test)

```bash
tsc --noEmit  # exits with 0 errors
```

### 7. Full End-to-End Flow (2 tests)

| Test | What It Checks |
|---|---|
| Backend returns complete valid response | Prediction, modalities, interpretation all in the correct format |
| History | Accumulates analyses over time on the backend |

---

## Running the Tests

```bash
bash /home/user/e2e_test.sh
```

The script checks every component and reports the final count. It can be run repeatedly on a clean run.

---

*Last updated: August 2026*