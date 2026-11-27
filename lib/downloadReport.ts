/**
 * BiofilmAI — Trigger a client-side Download Report for the Results page.
 * No API call, no UI change. Reads the analysis already shown on the
 * Results page (sessionStorage). Builds a PDF in the browser using
 * `lib/reportPdf.ts` and saves it as `BiofilmAI_Report_<analysisId>.pdf`.
 *
 * The report is written for clinicians: sample details, the result in plain
 * language, the evidence and clinical information entered, and limitations.
 * NO data is invented — only the data already in sessionStorage is rendered.
 * Errors are surfaced to the caller so the UI can show a message.
 */
import { buildReportPdf, ReportPayload, ReportResult, ReportRow } from "./reportPdf";
import { AnalysisResponse } from "./types";
import { clinicalLabel, RISK_MEANING } from "./clinicalLabels";
import { getDoctor } from "./auth";
import { formatDateTime } from "./utils";

export interface DownloadReportInput extends AnalysisResponse {
  sampleInfo?: {
    sampleId?: string; studyId?: string; sampleType?: string; collectionDate?: string;
    infectionContext?: string; woundOrImplant?: string; notes?: string;
  } | null;
}

export class DownloadReportError extends Error {
  status: "noData" | "buildFailed" | "browserFailed";
  constructor(status: "noData" | "buildFailed" | "browserFailed", message: string) {
    super(message);
    this.status = status;
  }
}

/**
 * Build a ReportPayload from analysis + request data already stored
 * in sessionStorage. Nothing is invented: any unknown field renders as "—".
 */
export function buildAnalysisPayload(
  raw: string | null,
  sampleRaw: string | null,
): { payload: ReportPayload; analysisId: string } {
  if (!raw) throw new DownloadReportError("noData", "No analysis data available for report.");
  let analysis: AnalysisResponse | any;
  let sample: DownloadReportInput["sampleInfo"] | null = null;
  let clinical: any = {};
  try { analysis = JSON.parse(raw); }
  catch { throw new DownloadReportError("noData", "Stored analysis data is corrupted."); }
  if (sampleRaw) {
    // The Analyze page stores { sampleInfo, clinicalData }.
    try {
      const req = JSON.parse(sampleRaw);
      sample = req?.sampleInfo ?? req;
      clinical = req?.clinicalData ?? {};
    } catch { sample = null; }
  }

  const safeStr = (v: unknown): string => (v === undefined || v === null || v === "") ? "—" : String(v);

  const demoFlag = !!analysis?.demoMode;
  const analysisId = safeStr(analysis?.analysisId ?? "unknown");
  const doctor = getDoctor();
  const when = analysis?.completedAt || analysis?.createdAt;

  const meta: string[] = [];
  if (doctor) meta.push("Requested by " + doctor.name);
  if (when) meta.push("Analysed " + formatDateTime(when));
  meta.push("Analysis ID " + analysisId);
  const sampleId = sample?.sampleId ?? analysis?.sampleId;
  const subtitle = sampleId ? `Sample ${sampleId}${sample?.sampleType ? "  -  " + sample.sampleType : ""}` : undefined;

  const banner = demoFlag
    ? "DEMO MODE: the result in this report is a simulated value from a research prototype. "
      + "It is not a clinical diagnosis and must not be used for patient care."
    : analysis?.modelMode === "evidence_score"
    ? "EVIDENCE SCORE: the score combines the indicators measured from the uploaded files. "
      + "It is not a clinical diagnosis and must not be used for patient care."
    : undefined;

  const sections: ReportRow[] = [];

  sections.push({
    heading: "Sample",
    fields: [
      { label: "Sample ID", value: safeStr(sample?.sampleId ?? analysis?.sampleId) },
      { label: "Study ID", value: safeStr(sample?.studyId) },
      { label: "Sample type", value: safeStr(sample?.sampleType ?? analysis?.sampleType) },
      { label: "Collection date", value: safeStr(sample?.collectionDate) },
      { label: "Wound / implant", value: safeStr(sample?.woundOrImplant) },
      { label: "Notes", value: safeStr(sample?.notes) },
    ],
  });

  const prob = analysis?.prediction?.biofilmProbability;
  const category: string | undefined = analysis?.prediction?.riskCategory;
  const categoryName = category ? category.charAt(0).toUpperCase() + category.slice(1) : undefined;
  const result: ReportResult | undefined = prob === undefined ? undefined : {
    percent: `${Math.round(Number(prob) * 100)}%`,
    category,
    label: `${categoryName ? categoryName + " risk" : "Risk"}${demoFlag ? " (simulated)" : ""}`,
    meaning: category ? RISK_MEANING[category] : undefined,
  };

  const has = (k: string) => !!analysis?.modalities?.[k]?.available;
  const provided = (k: string) => has(k) ? "Provided" : "Not provided";
  if (analysis?.evidence) {
    sections.push(...evidenceSections(analysis));
  } else {
    sections.push({
      heading: "Evidence used",
      fields: [
        { label: "Microscopy image", value: provided("microscopy") },
        { label: "Raman spectrum", value: provided("spectroscopy") },
        { label: "Genome sequence", value: provided("genomics") },
        { label: "Clinical information", value: provided("clinical") },
      ],
    });
  }

  sections.push({
    heading: "Clinical information",
    fields: [
      { label: "Infection context", value: clinicalLabel("infectionContext", clinical.infectionContext) },
      { label: "Implant present", value: clinical.implantPresent === undefined ? "—" : (clinical.implantPresent ? "Yes" : "No") },
      { label: "Sample site", value: safeStr(clinical.sampleSite) },
      { label: "Duration (days)", value: safeStr(clinical.chronicityDays) },
      { label: "Previous treatment", value: clinicalLabel("previousTreatment", clinical.previousTreatment) },
      { label: "Previous culture", value: clinicalLabel("previousCulture", clinical.previousCulture) },
      { label: "Additional notes", value: safeStr(clinical.additionalNotes) },
    ],
  });

  const payload: ReportPayload = {
    title: "Sample Report",
    subtitle,
    meta,
    banner,
    result,
    sections,
    footer: "BiofilmAI is a research prototype. It has not been clinically validated and is not a medical device. "
           + "This report does not replace culture, laboratory testing or clinical judgment, and must not be used "
           + "for diagnosis or treatment decisions.",
  };
  return { payload, analysisId };
}

/** Report sections for the measurements made on each uploaded file (backend/evidence.py). */
function evidenceSections(analysis: AnalysisResponse): ReportRow[] {
  const ev = analysis.evidence ?? {};
  const rows: ReportRow[] = [];
  const pct = (v: number) => `${Math.round(v * 100)}%`;

  if (analysis.findings?.length) {
    rows.push({
      heading: "Key findings",
      fields: analysis.findings.map((f, i) => ({ label: `Finding ${i + 1}`, value: f })),
    });
  }

  const parts = analysis.scoreBreakdown ?? [];
  if (parts.length) {
    rows.push({
      heading: "How the score was calculated (average of measured indicators)",
      fields: [
        ...parts.map((p) => ({ label: p.label, value: pct(p.indicator) })),
        { label: "Score", value: pct(analysis.prediction?.biofilmProbability ?? 0) },
      ],
    });
  }

  const m = ev.microscopy;
  if (m) {
    rows.push("error" in m
      ? { heading: "Microscopy image", fields: [{ label: "Result", value: m.error }] }
      : {
          heading: "Microscopy image analysis",
          fields: [
            { label: "Pattern", value: m.pattern_text },
            { label: "Surface covered", value: `${m.coverage_pct}%` },
            { label: "Cells in clusters", value: `${m.clustered_biomass_pct}%` },
            { label: "Clusters", value: `${m.cluster_count} (plus ${m.micro_colony_count} micro-colonies)` },
            ...(m.live_pct !== null ? [{ label: "Live cells", value: `${m.live_pct}%` }] : []),
            ...(m.matrix_pct !== null ? [{ label: "Matrix (EPS) stain", value: `${m.matrix_pct}% of the image` }] : []),
          ],
        });
  }

  const s = ev.spectroscopy;
  if (s) {
    rows.push("error" in s
      ? { heading: "Raman spectrum", fields: [{ label: "Result", value: s.error }] }
      : {
          heading: "Raman spectrum analysis",
          fields: [
            { label: "Matrix signal", value: `${s.matrix_text} (ratio ${s.matrix_ratio ?? "-"})` },
            { label: "Signal quality", value: `${s.quality} (signal-to-noise ${s.snr})` },
            ...s.peaks.map((p) => ({ label: `Peak ${p.wavenumber} cm-1`, value: p.assignment })),
          ],
        });
  }

  const g = ev.genomics;
  if (g) {
    if ("error" in g) {
      rows.push({ heading: "Genome", fields: [{ label: "Result", value: g.error }] });
    } else {
      const model = g.genomic_model;
      rows.push({
        heading: "Genome analysis",
        fields: [
          { label: "Genome size", value: `${(g.length_bp / 1e6).toFixed(2)} Mb, ${g.contigs} contigs, N50 ${(g.n50_bp / 1000).toFixed(0)} kb` },
          { label: "GC content", value: `${g.gc_pct}%` },
          ...g.markers.map((mk) => ({
            label: `Gene ${mk.gene}`,
            value: `${mk.present ? "FOUND" : "Not found"} (${mk.coverage_pct}% match) - ${mk.role}`,
          })),
          {
            label: "Genomic model",
            value: model.status === "completed"
              ? `Predicted ${model.predicted_class} S. epidermidis (P = ${Math.round((model.probability_pathogenic ?? 0) * 100)}%)`
              : "Not run: genome outside the model's training data (S. epidermidis only)",
          },
        ],
      });
    }
  }

  const c = ev.clinical;
  if (c) {
    rows.push({
      heading: `Clinical risk factors (${c.present_count} of ${c.total} present)`,
      fields: c.factors.map((f) => ({ label: f.present ? "Present" : "Absent", value: f.factor })),
    });
  }
  return rows;
}

export function downloadAnalysisReport(): void {
  const raw =
    typeof window !== "undefined" ? sessionStorage.getItem("biofilm-last-result") : null;
  const sampleRaw =
    typeof window !== "undefined" ? sessionStorage.getItem("biofilm-last-request") : null;
  let parsed: { payload: ReportPayload; analysisId: string };
  try {
    parsed = buildAnalysisPayload(raw, sampleRaw);
  } catch (e: unknown) {
    const err = e instanceof DownloadReportError
      ? e
      : new DownloadReportError("noData", (e as Error)?.message || "Unknown error");
    throw err;
  }

  let build: ReturnType<typeof buildReportPdf>;
  try {
    build = buildReportPdf(parsed.payload);
  } catch (e: unknown) {
    throw new DownloadReportError("buildFailed", "Failed to assemble PDF: " + ((e as Error)?.message || "unknown"));
  }

  if (!build?.bytes || build.bytes.length < 200) {
    throw new DownloadReportError("buildFailed", "Generated PDF is empty or invalid.");
  }

  const filename = `BiofilmAI_Report_${parsed.analysisId}.pdf`;
  try {
    // Detect a Blob-compatible global for the browser environment
    const B = (typeof window !== "undefined" ? window : globalThis) as unknown as {
      Blob?: typeof Blob;
      URL?: { createObjectURL?: (b: unknown) => string; revokeObjectURL?: (u: string) => void };
    };
    if (typeof B.Blob === "undefined" || !B.URL?.createObjectURL) {
      throw new DownloadReportError("browserFailed", "Browser does not support Blob download.");
    }
    const blob = new B.Blob([build.bytes as BlobPart], { type: "application/pdf" });
    const url = B.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.rel = "noopener";
    a.style.display = "none";
    document.body.appendChild(a);
    a.click();
    setTimeout(() => {
      try { B.URL?.revokeObjectURL?.(url); } catch { /* ignore */ }
      try { a.remove(); } catch { /* ignore */ }
    }, 1200);
  } catch (e: unknown) {
    throw new DownloadReportError("browserFailed", "Download failed: " + ((e as Error)?.message || "unknown"));
  }
}
