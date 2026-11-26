/**
 * BiofilmAI — Minimal, dependency-free PDF report builder
 * (multi-page, Helvetica Type1, used by the Results page "Download Report"
 *  button).
 *
 * The download builder is intentionally conservative:
 *  - Letter-size pages, continuing onto new pages as needed
 *  - standard Helvetica / Helvetica-Bold, no embedded fonts, no images
 *  - plain text positioning (no font metrics — uses character-count wrap)
 *  - simple vector shapes for the header band, result box and dividers
 *  - text is encoded as ASCII (common punctuation mapped, rest becomes "?")
 *
 * Only the data passed in is rendered. Nothing is invented.
 */

export type ReportField = { label: string; value: string };

export type ReportRow = { heading: string; fields: ReportField[] };

export type ReportResult = {
  percent: string;            // e.g. "79%"
  category?: string;          // "low" | "intermediate" | "high"
  label: string;              // e.g. "High risk - simulated"
  meaning?: string;           // plain-language explanation
};

export type ReportPayload = {
  title: string;
  subtitle?: string;
  meta?: string[];            // short lines shown at the right of the header
  banner?: string;            // e.g. "DEMO MODE — ..."
  result?: ReportResult;      // highlighted result box
  sections: ReportRow[];
  footer?: string;
};

// ── Geometry (1pt = 1/72 inch) ─────────────────────────────────────────
const PW = 612;          // 8.5″
const PH = 792;          // 11″
const MARGIN_L = 54;     // 0.75″
const MARGIN_R = 54;
const MARGIN_B = 50;
const LINE = 14;         // 10pt + ~4 leading
const CONTENT_W = PW - MARGIN_L - MARGIN_R;
const VALUE_X = MARGIN_L + 150;

type RGB = [number, number, number];
const TEAL: RGB = [0.09, 0.42, 0.53];
const INK: RGB = [0.09, 0.19, 0.25];
const MUTED: RGB = [0.38, 0.47, 0.52];
const RULE: RGB = [0.86, 0.91, 0.93];
const WHITE: RGB = [1, 1, 1];
const RISK_COLORS: Record<string, { fill: RGB; edge: RGB; text: RGB }> = {
  low: { fill: [0.91, 0.96, 0.94], edge: [0.18, 0.55, 0.45], text: [0.12, 0.42, 0.34] },
  intermediate: { fill: [0.99, 0.95, 0.88], edge: [0.85, 0.60, 0.17], text: [0.62, 0.40, 0.05] },
  high: { fill: [0.99, 0.92, 0.92], edge: [0.79, 0.30, 0.30], text: [0.62, 0.18, 0.18] },
};

function escapePdf(s: string): string {
  return s
    .replace(/[–—]/g, "-")
    .replace(/•/g, "*")
    .replace(/[‘’]/g, "'")
    .replace(/[“”]/g, '"')
    .replace(/\\/g, "\\\\")
    .replace(/\(/g, "\\(")
    .replace(/\)/g, "\\)")
    .replace(/[\r\n\t]+/g, " ")
    .replace(/[^\x20-\x7e]/g, "?");
}

function wrap(text: string, maxChars: number): string[] {
  const words = text.split(/\s+/).filter(Boolean);
  if (words.length === 0) return [""];
  const out: string[] = [];
  let cur = "";
  for (const w of words) {
    const cand = cur.length === 0 ? w : cur + " " + w;
    if (cand.length > maxChars) {
      if (cur.length > 0) { out.push(cur); cur = ""; }
      let rest = w;
      while (rest.length > maxChars) {
        out.push(rest.slice(0, maxChars));
        rest = rest.slice(maxChars);
      }
      cur = rest;
    } else {
      cur = cand;
    }
  }
  if (cur.length > 0) out.push(cur);
  return out;
}

// Rough Helvetica text width (average glyph ≈ 0.5em), used for right alignment.
function approxWidth(text: string, size: number): number {
  return text.length * size * 0.5;
}

// ───────────────────────────────────────────────────────────────────────────
// PDF builder (sequential, dependency-free)
// ───────────────────────────────────────────────────────────────────────────

type TextOp = { kind: "text"; x: number; y: number; size: number; text: string; bold?: boolean; color?: RGB };
type RectOp = { kind: "rect"; x: number; y: number; w: number; h: number; fill: RGB; stroke?: RGB };
type LineOp = { kind: "line"; x1: number; y1: number; x2: number; y2: number; color: RGB; width: number };
type Op = TextOp | RectOp | LineOp;

interface BuildResult { bytes: Uint8Array; warnings: string[]; }

const rgb = (c: RGB) => c.map((v) => v.toFixed(3)).join(" ");

export function buildReportPdf(payload: ReportPayload): BuildResult {
  const warnings: string[] = [];
  const pages: Op[][] = [[]];
  let OP: Op[] = pages[0];

  const HEADER_H = 78;
  const footerLines = payload.footer ? wrap(payload.footer, 100) : [];
  const bottomLimit = MARGIN_B + footerLines.length * 11 + 20;
  let y = 0;

  // Header band: full on the first page, a slim strip on later pages.
  function header(first: boolean): void {
    if (first) {
      OP.push({ kind: "rect", x: 0, y: PH - HEADER_H, w: PW, h: HEADER_H, fill: TEAL });
      OP.push({ kind: "text", x: MARGIN_L, y: PH - 38, size: 20, bold: true, text: "BiofilmAI", color: WHITE });
      OP.push({ kind: "text", x: MARGIN_L, y: PH - 58, size: 11, text: payload.title, color: [0.85, 0.94, 0.96] });
      (payload.meta ?? []).slice(0, 3).forEach((m, i) => {
        OP.push({ kind: "text", x: PW - MARGIN_R - approxWidth(m, 9), y: PH - 32 - i * 13, size: 9, text: m, color: [0.85, 0.94, 0.96] });
      });
      y = PH - HEADER_H - 26;
    } else {
      OP.push({ kind: "rect", x: 0, y: PH - 8, w: PW, h: 8, fill: TEAL });
      OP.push({ kind: "text", x: MARGIN_L, y: PH - 34, size: 9, bold: true, text: "BiofilmAI  " + payload.title + " (continued)", color: MUTED });
      y = PH - 56;
    }
  }

  // Start a new page when the next block would not fit.
  function ensure(height: number): void {
    if (y - height >= bottomLimit) return;
    OP = [];
    pages.push(OP);
    header(false);
  }

  header(true);

  // Subtitle (e.g. who requested the report)
  if (payload.subtitle) {
    OP.push({ kind: "text", x: MARGIN_L, y, size: 10, text: payload.subtitle, color: MUTED });
    y -= 22;
  }

  // Demo / warning banner: amber box with a darker left edge
  if (payload.banner) {
    const lines = wrap(payload.banner, 92);
    const bh = 14 + lines.length * 12;
    ensure(bh);
    OP.push({ kind: "rect", x: MARGIN_L, y: y - bh + 10, w: CONTENT_W, h: bh, fill: [0.99, 0.96, 0.89] });
    OP.push({ kind: "rect", x: MARGIN_L, y: y - bh + 10, w: 4, h: bh, fill: [0.85, 0.60, 0.17] });
    lines.forEach((l, i) => OP.push({
      kind: "text", x: MARGIN_L + 14, y: y - 4 - i * 12, size: 9, text: l,
      color: [0.50, 0.33, 0.04],
    }));
    y -= bh + 14;
  }

  // Result box: big percentage, risk label and meaning, coloured by category
  if (payload.result) {
    const r = payload.result;
    const c = RISK_COLORS[r.category ?? ""] ?? { fill: [0.94, 0.97, 0.98] as RGB, edge: TEAL, text: TEAL };
    const meaning = r.meaning ? wrap(r.meaning, 58) : [];
    const bh = Math.max(64, 34 + meaning.length * 12);
    ensure(bh + 10);
    const top = y + 10;
    OP.push({ kind: "rect", x: MARGIN_L, y: top - bh, w: CONTENT_W, h: bh, fill: c.fill, stroke: c.edge });
    OP.push({ kind: "text", x: MARGIN_L + 16, y: top - 22, size: 8, bold: true, text: "BIOFILM-ASSOCIATED RISK", color: MUTED });
    OP.push({ kind: "text", x: MARGIN_L + 16, y: top - 50, size: 26, bold: true, text: r.percent, color: c.text });
    OP.push({ kind: "text", x: MARGIN_L + 160, y: top - 24, size: 13, bold: true, text: r.label, color: c.text });
    meaning.forEach((l, i) => OP.push({ kind: "text", x: MARGIN_L + 160, y: top - 40 - i * 12, size: 9.5, text: l, color: INK }));
    y = top - bh - 22;
  }

  for (const section of payload.sections) {
    ensure(LINE * 4); // keep a heading together with its first rows
    OP.push({ kind: "text", x: MARGIN_L, y, size: 9, bold: true, text: section.heading.toUpperCase(), color: TEAL });
    OP.push({ kind: "line", x1: MARGIN_L, y1: y - 6, x2: PW - MARGIN_R, y2: y - 6, color: TEAL, width: 0.8 });
    y -= 20;
    for (const f of section.fields) {
      const valStr = (f.value === undefined || f.value === null || f.value === "") ? "-" : String(f.value);
      const labelLines = wrap(f.label, 26);
      const valueLines = wrap(valStr, 62);
      const rows = Math.max(labelLines.length, valueLines.length);
      ensure(LINE * rows + 4);
      labelLines.forEach((l, i) => OP.push({ kind: "text", x: MARGIN_L, y: y - i * LINE, size: 9.5, text: l, color: MUTED }));
      valueLines.forEach((l, i) => OP.push({ kind: "text", x: VALUE_X, y: y - i * LINE, size: 10, text: l, color: INK }));
      y -= LINE * rows - 7;
      OP.push({ kind: "line", x1: MARGIN_L, y1: y, x2: PW - MARGIN_R, y2: y, color: RULE, width: 0.5 });
      y -= 11;
    }
    y -= 8;
  }

  // Footer and page number on every page
  pages.forEach((ops, i) => {
    const top = MARGIN_B + footerLines.length * 11 + 4;
    ops.push({ kind: "line", x1: MARGIN_L, y1: top + 8, x2: PW - MARGIN_R, y2: top + 8, color: RULE, width: 0.5 });
    footerLines.forEach((l, j) => ops.push({ kind: "text", x: MARGIN_L, y: top - 6 - j * 11, size: 8, text: l, color: MUTED }));
    const pn = `Page ${i + 1} of ${pages.length}`;
    ops.push({ kind: "text", x: PW - MARGIN_R - approxWidth(pn, 8), y: top - 6, size: 8, text: pn, color: MUTED });
  });

  // ───── Encode the PDF to bytes ─────
  // Objects: 1 Catalog, 2 Pages, 3 Helvetica, 4 Helvetica-Bold, then a
  // Page + Contents pair per page.
  const bytes: number[] = [];

  // Append a string as single bytes (content is already ASCII after escapePdf).
  function append(s: string): void {
    for (let i = 0; i < s.length; i++) {
      const c = s.charCodeAt(i);
      bytes.push(c === 0x0a || (c >= 0x20 && c <= 0x7e) ? c : 0x3f);
    }
  }

  const objCount = 4 + pages.length * 2;
  const off: number[] = new Array(objCount + 1).fill(0);
  const pageId = (i: number) => 5 + i * 2;
  const contentId = (i: number) => 6 + i * 2;

  append("%PDF-1.4\n");

  off[1] = bytes.length;
  append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n");

  off[2] = bytes.length;
  const kids = pages.map((_, i) => `${pageId(i)} 0 R`).join(" ");
  append(`2 0 obj\n<< /Type /Pages /Kids [${kids}] /Count ${pages.length} >>\nendobj\n`);

  off[3] = bytes.length;
  append("3 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>\nendobj\n");

  off[4] = bytes.length;
  append("4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>\nendobj\n");

  pages.forEach((ops, i) => {
    const parts: string[] = [];
    // Shapes first, then text on top.
    for (const op of ops) {
      if (op.kind === "rect") {
        parts.push(`${rgb(op.fill)} rg`);
        if (op.stroke) parts.push(`${rgb(op.stroke)} RG 0.8 w ${op.x} ${op.y} ${op.w} ${op.h} re B`);
        else parts.push(`${op.x} ${op.y} ${op.w} ${op.h} re f`);
      } else if (op.kind === "line") {
        parts.push(`${rgb(op.color)} RG ${op.width} w ${op.x1} ${op.y1} m ${op.x2} ${op.y2} l S`);
      }
    }
    parts.push("BT");
    for (const op of ops) {
      if (op.kind !== "text") continue;
      parts.push(
        `${rgb(op.color ?? INK)} rg`,
        `/${op.bold ? "F2" : "F1"} ${op.size} Tf`,
        `1 0 0 1 ${op.x.toFixed(1)} ${op.y.toFixed(1)} Tm`,
        `(${escapePdf(op.text)}) Tj`,
      );
    }
    parts.push("ET");
    const stream = parts.join("\n");

    off[pageId(i)] = bytes.length;
    append(`${pageId(i)} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 ${PW} ${PH}] ` +
      `/Resources << /Font << /F1 3 0 R /F2 4 0 R >> /ProcSet [/PDF /Text] >> /Contents ${contentId(i)} 0 R >>\nendobj\n`);

    off[contentId(i)] = bytes.length;
    append(`${contentId(i)} 0 obj\n<< /Length ${stream.length} >>\nstream\n${stream}\nendstream\nendobj\n`);
  });

  // Cross-reference table: one 20-byte entry per object, "offset generation n".
  const xrefOffset = bytes.length;
  append(`xref\n0 ${objCount + 1}\n0000000000 65535 f \n`);
  for (let n = 1; n <= objCount; n++) {
    append(`${off[n].toString().padStart(10, "0")} 00000 n \n`);
  }
  append(`trailer\n<< /Size ${objCount + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`);

  if (pages.length > 1) warnings.push(`Report spans ${pages.length} pages.`);
  return { bytes: new Uint8Array(bytes), warnings };
}
