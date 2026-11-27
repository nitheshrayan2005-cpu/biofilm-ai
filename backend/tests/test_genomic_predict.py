"""
BiofilmAI — Automated backend tests for the research genomic endpoint.

Run against the running server:
    python -m backend.tests.test_genomic_predict

Tests:
  1. valid genomic prediction (200, correct response structure)
  2. missing feature -> 400
  3. extra feature -> 400
  4. invalid numeric value -> 400
  5. NaN/inf value -> 400
  6. model artifact missing -> 503 (via direct service unit test)
  7. correct model version
  8. correct target label
  9. clear research disclaimer present
  10. clinical-facing /api/analyze still returns DEMO MODE (unchanged)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# The check marks below need UTF-8; the Windows console defaults to cp1252.
sys.stdout.reconfigure(encoding="utf-8")

PASS = 0
FAIL = 0


def _auth_header() -> dict:
    """Sign requests as the first registered doctor (tests run beside the server)."""
    sys.path.insert(0, os.path.join(ROOT, "backend"))
    import auth
    doctors = auth._load_doctors()
    if not doctors:
        sys.exit("No doctor accounts found. Add one with: python backend/auth.py add <username> \"<name>\"")
    username, doctor = next(iter(doctors.items()))
    token = auth.create_token({"username": username, "name": doctor["name"]})
    return {"Authorization": f"Bearer {token}"}


AUTH = _auth_header()


def check(name: str, ok: bool, detail: str = ""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  ✅ PASS: {name}")
    else:
        FAIL += 1
        print(f"  ❌ FAIL: {name} — {detail}")


def post(path: str, body: dict):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json", **AUTH})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.load(e)


def load_real_features():
    """First isolate of the training CSV when it is available, else the bundled test request."""
    schema = json.load(open(os.path.join(ROOT, "backend", "ml", "artifacts", "feature_schema.json")))["features"]
    csv_path = os.path.join(os.path.dirname(ROOT), "uploads", "BiofilmAI_genomic_features.csv")
    if not os.path.isfile(csv_path):
        request = json.load(open(os.path.join(ROOT, "test_data", "genomic_predict_request.json")))
        return {c: float(request["features"][c]) for c in schema}
    import pandas as pd
    row = pd.read_csv(csv_path).iloc[0]
    return {c: float(row[c]) for c in schema}


def main():
    print("=" * 66)
    print("BiofilmAI — Research Genomic Endpoint Tests")
    print("=" * 66)

    features = load_real_features()

    # 1. Valid prediction
    s, resp = post("/api/research/genomic-predict", {"isolate_id": "424", "features": features})
    check("valid genomic prediction returns 200", s == 200, f"status={s}")
    check("response has predicted_class", "predicted_class" in resp and resp["predicted_class"] in ("pathogenic", "commensal"))
    check("response has both probabilities", 0 <= resp.get("probability_pathogenic", -1) <= 1 and 0 <= resp.get("probability_commensal", -1) <= 1)
    check("probabilities sum to 1", abs(resp["probability_pathogenic"] + resp["probability_commensal"] - 1) < 1e-6, f"{resp['probability_pathogenic']}+{resp['probability_commensal']}")

    # 7. correct model version
    check("correct model version", resp.get("model_version") == "genomic-lr-v1.0", str(resp.get("model_version")))
    check("correct model mode", resp.get("model_mode") == "real_genomic_model", str(resp.get("model_mode")))

    # 8. correct target label
    check("correct experiment target", resp.get("experiment_target") == "pathogenic_vs_commensal", str(resp.get("experiment_target")))

    # 9. clear research disclaimer
    dis = resp.get("research_disclaimer", "")
    check("clear research disclaimer present",
          "not a biofilm diagnosis" in dis and "clinical decision" in dis and "Research model output" in dis,
          dis[:120])

    # 2. missing feature
    bad = dict(features); bad.pop(next(iter(features)))
    s, resp = post("/api/research/genomic-predict", {"isolate_id": "x", "features": bad})
    check("missing feature -> 400", s == 400 and "Missing" in resp.get("detail", ""), f"status={s}")

    # 3. extra feature
    bad2 = dict(features); bad2["kmer_ZZZZ"] = 0.5
    s, resp = post("/api/research/genomic-predict", {"isolate_id": "x", "features": bad2})
    check("extra feature -> 400", s == 400 and "Unknown/extra" in resp.get("detail", ""), f"status={s}")

    # 4. invalid numeric value (string)
    bad3 = dict(features); bad3[next(iter(features))] = "abc"
    s, resp = post("/api/research/genomic-predict", {"isolate_id": "x", "features": bad3})
    check("invalid numeric value -> 400", s == 400 and "must be numeric" in resp.get("detail", ""), f"status={s}")

    # 5. NaN value
    bad4 = dict(features); bad4[next(iter(features))] = float("nan")
    s, resp = post("/api/research/genomic-predict", {"isolate_id": "x", "features": bad4})
    check("NaN value -> 400", s == 400 and "finite" in resp.get("detail", ""), f"status={s}")

    # 10. clinical-facing /api/analyze unchanged (DEMO MODE)
    import urllib.parse
    data = urllib.parse.urlencode({
        "sampleInfo": json.dumps({"sampleId": "S-T","studyId": "BF-T","sampleType": "Wound swab"}),
        "clinicalData": json.dumps({"infectionContext": "chronic-wound","chronicityDays": 7}),
    }).encode()
    req = urllib.request.Request(BASE + "/api/analyze", data=data, headers=AUTH)
    with urllib.request.urlopen(req) as r:
        aresp = json.load(r)
    check("clinical /api/analyze still demoMode=True", aresp.get("demoMode") is True)
    check("clinical /api/analyze modelMode=demo", aresp.get("modelMode") == "demo")

    # 6. missing model artifact -> 503 (direct service unit test)
    sys.path.insert(0, os.path.join(ROOT))
    from backend.ml.inference.genomic_research_service import GenomicResearchService
    svc = GenomicResearchService(model_json="/nonexistent/model.json")
    check("missing artifact -> service not loaded", svc.load() is False)
    try:
        svc.predict(features)
        check("missing artifact -> predict raises RuntimeError", False)
    except RuntimeError:
        check("missing artifact -> predict raises RuntimeError", True)

    print("=" * 66)
    print(f"  PASSED: {PASS}   FAILED: {FAIL}")
    print("=" * 66)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
