"""
BiofilmAI - End-to-end API check using the files in test_data/.

Start the backend first, then run from the project root:
    .venv\\Scripts\\python.exe test_data\\run_e2e_test.py
    .venv\\Scripts\\python.exe test_data\\run_e2e_test.py http://localhost:8001

The API requires a doctor login. The script asks for a username and password,
or reads them from the BIOFILM_TEST_USER / BIOFILM_TEST_PASSWORD environment
variables. Create an account with:  python backend\\auth.py add <username> "<Name>"

Uses only the standard library.
"""

from __future__ import annotations

import getpass
import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")

PASS = FAIL = SKIP = 0
TOKEN: str | None = None


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASS, FAIL
    PASS, FAIL = (PASS + 1, FAIL) if ok else (PASS, FAIL + 1)
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  - {detail}" if detail and not ok else ""))


def skip(name: str, reason: str) -> None:
    global SKIP
    SKIP += 1
    print(f"  [SKIP] {name}  - {reason}")


def request(method: str, path: str, body: bytes | None = None, headers: dict | None = None, auth: bool = True):
    headers = dict(headers or {})
    if auth and TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def post_json(path: str, payload, auth: bool = True) -> tuple:
    return request("POST", path, json.dumps(payload).encode(), {"Content-Type": "application/json"}, auth)


def post_multipart(path: str, fields: dict, files: dict) -> tuple:
    boundary = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    for k, p in files.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"; filename="{p.name}"\r\n'
            f"Content-Type: application/octet-stream\r\n\r\n".encode() + p.read_bytes() + b"\r\n"
        )
    body = b"".join(parts) + f"--{boundary}--\r\n".encode()
    return request("POST", path, body, {"Content-Type": f"multipart/form-data; boundary={boundary}"})


def credentials() -> tuple[str, str]:
    user = os.getenv("BIOFILM_TEST_USER") or input("Doctor username: ").strip()
    password = os.getenv("BIOFILM_TEST_PASSWORD") or getpass.getpass("Password: ")
    return user, password


SAMPLE_INFO = {
    "sampleId": "S-TEST-001",
    "studyId": "BF-E2E-2026",
    "sampleType": "Implant sonicate",
    "collectionDate": "2026-10-15",
    "infectionContext": "Orthopedic implant",
    "woundOrImplant": "Knee prosthesis",
    "notes": "Synthetic end-to-end test sample",
}
CLINICAL = {
    "infectionContext": "orthopedic-implant",
    "chronicityDays": 120,
    "implantPresent": True,
    "sampleSite": "Knee (prosthetic)",
    "previousTreatment": "antibiotics",
    "previousCulture": "positive-pure",
    "additionalNotes": "Synthetic test data",
}


def main() -> int:
    global TOKEN
    if not (HERE / "microscopy_biofilm.png").exists():
        print("Test files missing - run test_data/generate_test_data.py first.")
        return 1
    print(f"BiofilmAI end-to-end test against {BASE}\n")

    print("1. Health")
    try:
        status, body = request("GET", "/api/health")
    except urllib.error.URLError as e:
        print(f"  Cannot reach backend: {e.reason}")
        return 1
    check("GET /api/health returns 200", status == 200)
    check("health response is BiofilmAI (has version + demo_mode)",
          isinstance(body, dict) and "version" in body and "demo_mode" in body,
          f"got {body} - is another app on this port?")

    print("\n2. Authentication")
    status, _ = request("GET", "/api/history", auth=False)
    check("protected endpoint without login returns 401", status == 401, f"got {status}")
    status, _ = post_json("/api/auth/login", {"username": f"nobody-{uuid.uuid4().hex[:8]}", "password": "wrong"}, auth=False)
    check("unknown user / wrong password returns 401", status == 401, f"got {status}")
    user, password = credentials()
    status, body = post_json("/api/auth/login", {"username": user, "password": password}, auth=False)
    check("doctor login returns 200 with a token", status == 200 and bool((body or {}).get("token")), str(body))
    if status != 200:
        print("\n  Cannot continue without a valid login.")
        print(f"\n{'=' * 50}\n  PASSED: {PASS}   FAILED: {FAIL}   SKIPPED: {SKIP}\n{'=' * 50}")
        return 1
    TOKEN = body["token"]

    print("\n3. Multimodal analysis (all 4 modalities)")
    status, res = post_multipart(
        "/api/analyze",
        {"sampleInfo": json.dumps(SAMPLE_INFO), "clinicalData": json.dumps(CLINICAL)},
        {"microscopy": HERE / "microscopy_biofilm.png",
         "spectroscopy": HERE / "spectroscopy_raman.csv",
         "genomics": HERE / "genomics_isolate.fasta"},
    )
    check("POST /api/analyze returns 200", status == 200, str(res))
    analysis_id = res.get("analysisId") if status == 200 else None
    if analysis_id:
        pred = res.get("prediction", {})
        prob = pred.get("biofilmProbability")
        check("analysis ID generated", bool(analysis_id))
        check("4 modalities in response", len(res.get("modalities", {})) == 4, str(res.get("modalities", {}).keys()))
        check("probability between 0 and 1", isinstance(prob, (int, float)) and 0 <= prob <= 1, str(prob))
        check("risk category valid", pred.get("riskCategory") in {"low", "intermediate", "high"})
        check("result is the rule-based evidence score", res.get("modelMode") == "evidence_score", str(res.get("modelMode")))
        ev = res.get("evidence") or {}
        check("evidence measured for all 4 modalities", set(ev) == {"microscopy", "spectroscopy", "genomics", "clinical"}, str(ev.keys()))
        check("key findings listed", len(res.get("findings") or []) > 0)
        parts = res.get("scoreBreakdown") or []
        check("score equals the average of its indicators",
              bool(parts) and abs(sum(p["indicator"] for p in parts) / len(parts) - prob) < 0.01, str(parts))
        print(f"     -> {analysis_id}: score={prob}, risk={pred.get('riskCategory')}")
        status, again = post_multipart(
            "/api/analyze",
            {"sampleInfo": json.dumps(SAMPLE_INFO), "clinicalData": json.dumps(CLINICAL)},
            {"microscopy": HERE / "microscopy_biofilm.png",
             "spectroscopy": HERE / "spectroscopy_raman.csv",
             "genomics": HERE / "genomics_isolate.fasta"},
        )
        check("same files give the same score", status == 200 and again["prediction"]["biofilmProbability"] == prob)

    print("\n3b. Evidence from real genomes and images")
    cases = [
        ("Test_1_MRSA_knee_implant_REAL", True, True),
        ("Test_8_Sepidermidis_ATCC12228_commensal_REAL", False, False),
    ]
    for folder, mec, ica in cases:
        genome = HERE / "sample_tests" / folder / "3_genomics.fasta"
        if not genome.exists():
            skip(f"{folder} genome", "sample folder not present")
            continue
        status, res = post_multipart(
            "/api/analyze",
            {"sampleInfo": json.dumps({**SAMPLE_INFO, "sampleId": folder[:20]}), "clinicalData": json.dumps(CLINICAL)},
            {"genomics": genome},
        )
        g = ((res or {}).get("evidence") or {}).get("genomics") or {}
        check(f"{folder}: mecA {'found' if mec else 'absent'}, ica {'found' if ica else 'absent'}",
              status == 200 and g.get("mecA") is mec and g.get("ica_operon") is ica, str({k: g.get(k) for k in ('mecA', 'ica_operon')}))
    for case, pattern in (("case_1_mature_implant_biofilm", "dense_clusters"), ("case_3_planktonic_no_biofilm", "scattered")):
        image = HERE / "demo_samples" / case / "microscopy.png"
        status, res = post_multipart(
            "/api/analyze",
            {"sampleInfo": json.dumps({**SAMPLE_INFO, "sampleId": case[:20]}), "clinicalData": json.dumps(CLINICAL)},
            {"microscopy": image},
        )
        m = ((res or {}).get("evidence") or {}).get("microscopy") or {}
        check(f"{case}: microscopy pattern is {pattern}", status == 200 and m.get("pattern") == pattern, str(m.get("pattern")))

    print("\n4. Analysis with sample info + clinical only")
    status, _ = post_multipart(
        "/api/analyze",
        {"sampleInfo": json.dumps({**SAMPLE_INFO, "sampleId": "S-TEST-002"}),
         "clinicalData": json.dumps(CLINICAL)},
        {},
    )
    check("POST /api/analyze (no files) returns 200", status == 200)

    print("\n5. History & retrieval")
    status, hist = request("GET", "/api/history")
    check("GET /api/history returns 200", status == 200)
    if analysis_id:
        status, one = request("GET", f"/api/analysis/{analysis_id}")
        check("GET /api/analysis/{id} returns the analysis", status == 200 and one.get("analysisId") == analysis_id)

    print("\n6. Research: genomic classifier")
    payload = json.loads((HERE / "genomic_predict_request.json").read_text())
    status, g = post_json("/api/research/genomic-predict", payload)
    check("valid 343-feature request returns 200", status == 200, str(g)[:200])
    if status == 200:
        check("probabilities sum to 1",
              abs(g["probability_pathogenic"] + g["probability_commensal"] - 1) < 1e-6)
        print(f"     -> predicted={g['predicted_class']}, P(pathogenic)={g['probability_pathogenic']:.3f}")
    bad = dict(payload["features"]); bad.pop(next(iter(bad)))
    status, _ = post_json("/api/research/genomic-predict", {"features": bad})
    check("missing feature returns 400", status == 400, f"got {status}")

    print("\n7. Research: biofilm thickness")
    for case in json.loads((HERE / "thickness_requests.json").read_text()):
        status, t = post_json("/api/research/biofilm-thickness-predict", case)
        if status == 503:
            skip(f"{case}", "thickness model could not load on this machine (503)")
            continue
        check(f"{case} returns 200", status == 200, str(t))
        if status == 200:
            print(f"     -> predicted AVEG = {t['predicted_thickness']:.3f}")
    status, _ = post_json("/api/research/biofilm-thickness-predict", {"time": 2, "flow_rate_ul_min": 5, "channel": "FLAT"})
    check("time out of range returns 400", status == 400)
    status, _ = post_json("/api/research/biofilm-thickness-predict", {"time": 0.5, "flow_rate_ul_min": 5, "channel": "XYZ"})
    check("unknown channel returns 400", status == 400)

    print("\n8. Error handling")
    status, _ = post_multipart("/api/analyze", {"sampleInfo": "{}", "clinicalData": "{}"}, {})
    check("missing required sample fields returns 400", status == 400)
    status, _ = post_multipart(
        "/api/analyze",
        {"sampleInfo": json.dumps(SAMPLE_INFO), "clinicalData": json.dumps(CLINICAL)},
        {"microscopy": HERE / "invalid_microscopy.pdf"},
    )
    check(".pdf uploaded as microscopy returns 400", status == 400)
    status, _ = request("GET", "/api/analysis/NONEXISTENT")
    check("unknown analysis ID returns 404", status == 404)

    print(f"\n{'=' * 50}\n  PASSED: {PASS}   FAILED: {FAIL}   SKIPPED: {SKIP}\n{'=' * 50}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
