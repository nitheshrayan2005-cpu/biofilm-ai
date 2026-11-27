'use client';

// Results-page cards for the measurements made on each uploaded file
// (backend/evidence.py). Every card says what was measured and what it means.

import { CheckCircle2, CircleSlash, Lightbulb, Microscope, Atom, Dna, ClipboardList, AlertTriangle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, ReferenceDot } from 'recharts';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import {
  AnalysisResponse,
  ClinicalEvidence,
  GenomeEvidence,
  MicroscopyEvidence,
  ModalityName,
  SpectrumEvidence,
} from '@/lib/types';

const pct = (v: number) => `${Math.round(v * 100)}%`;

function Header({ icon: Icon, title, subtitle }: { icon: any; title: string; subtitle: string }) {
  return (
    <CardHeader>
      <div className="flex items-start gap-3">
        <div className="h-9 w-9 rounded-md bg-primary-50 text-primary flex items-center justify-center shrink-0">
          <Icon className="h-4 w-4" />
        </div>
        <div>
          <CardTitle>{title}</CardTitle>
          <p className="text-sm text-ink-secondary mt-0.5">{subtitle}</p>
        </div>
      </div>
    </CardHeader>
  );
}

function Stat({ label, value, hint }: { label: string; value: React.ReactNode; hint?: string }) {
  return (
    <div className="rounded-md border border-border-subtle bg-surface-muted/40 p-3">
      <p className="text-[11px] uppercase tracking-wider text-ink-secondary">{label}</p>
      <p className="mt-1 text-lg font-semibold text-ink tabular-nums">{value}</p>
      {hint && <p className="text-[11px] text-ink-secondary leading-snug">{hint}</p>}
    </div>
  );
}

function Meaning({ children }: { children: React.ReactNode }) {
  return (
    <p className="mt-4 rounded-md bg-primary-50/60 border border-primary-100 px-3 py-2 text-[13px] text-ink leading-relaxed">
      <span className="font-semibold">What this means: </span>
      {children}
    </p>
  );
}

// ── Summary ──────────────────────────────────────────────────────────────

type Tone = 'high' | 'medium' | 'low' | 'none';
const TONE: Record<Tone, { dot: string; text: string }> = {
  high: { dot: 'bg-danger', text: 'text-danger' },
  medium: { dot: 'bg-warning', text: 'text-warning-700' },
  low: { dot: 'bg-success', text: 'text-success' },
  none: { dot: 'bg-ink-secondary/40', text: 'text-ink-secondary' },
};

function tile(result: AnalysisResponse, key: ModalityName): { verdict: string; detail: string; tone: Tone } {
  const ev = result.evidence ?? {};
  const raw: any = (ev as any)[key];
  if (!raw) return { verdict: 'Not provided', detail: 'No data for this sample', tone: 'none' };
  if ('error' in raw) return { verdict: 'Could not be read', detail: 'Check the uploaded file', tone: 'none' };
  if (key === 'microscopy') {
    const m = raw as MicroscopyEvidence;
    return {
      dense_clusters: { verdict: 'Biofilm structure', detail: `${m.clustered_biomass_pct}% of cells clustered`, tone: 'high' as Tone },
      micro_colonies: { verdict: 'Early colonies', detail: `${m.micro_colony_count + m.cluster_count} small cell groups`, tone: 'medium' as Tone },
      scattered: { verdict: 'No biofilm structure', detail: 'Mostly single cells', tone: 'low' as Tone },
    }[m.pattern];
  }
  if (key === 'spectroscopy') {
    const s = raw as SpectrumEvidence;
    const v = { strong: ['Strong matrix signal', 'high'], moderate: ['Moderate matrix signal', 'medium'], weak: ['Weak matrix signal', 'low'], unknown: ['Not assessed', 'none'] }[s.matrix_level];
    return { verdict: v[0], detail: `Signal quality: ${s.quality}`, tone: v[1] as Tone };
  }
  if (key === 'genomics') {
    const g = raw as GenomeEvidence;
    const verdict = g.mecA && g.ica_operon ? 'Resistance + biofilm genes'
      : g.mecA ? 'Resistance gene (mecA)'
      : g.ica_operon ? 'Biofilm genes (ica)'
      : 'No key genes found';
    return { verdict, detail: `${(g.length_bp / 1e6).toFixed(2)} Mb genome · GC ${g.gc_pct}%`, tone: g.mecA || g.ica_operon ? 'high' : 'low' };
  }
  const c = raw as ClinicalEvidence;
  return {
    verdict: `${c.present_count} of ${c.total} risk factors`,
    detail: c.present_count >= 3 ? 'Typical biofilm setting' : c.present_count ? 'Some risk factors' : 'No risk factors',
    tone: c.present_count >= 3 ? 'high' : c.present_count ? 'medium' : 'low',
  };
}

/** One tile per evidence type with a single plain-language verdict. */
export function EvidenceSummary({ result }: { result: AnalysisResponse }) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {PARTS.map((p) => {
        const t = tile(result, p.key);
        return (
          <div key={p.key} className="rounded-xl border border-border bg-white p-5 shadow-card">
            <span className="inline-flex items-center gap-2 text-[12px] font-medium uppercase tracking-wider text-ink-secondary">
              <p.icon className="h-4 w-4 text-primary" /> {p.short}
            </span>
            <p className={`mt-3 flex items-center gap-2 text-[15px] font-semibold ${t.tone === 'none' ? 'text-ink-secondary' : 'text-ink'}`}>
              <span className={`h-2 w-2 rounded-full shrink-0 ${TONE[t.tone].dot}`} />
              {t.verdict}
            </p>
          </div>
        );
      })}
    </div>
  );
}

/** Closed by default; holds the full technical detail. */
export function Details({ children }: { children: React.ReactNode }) {
  return (
    <details className="group rounded-xl border border-border bg-white shadow-card">
      <summary className="flex cursor-pointer list-none items-center justify-between px-5 py-4 text-sm font-semibold text-ink">
        View detailed measurements
        <span className="text-ink-secondary text-xs font-normal group-open:hidden">Charts, gene table, risk checklist</span>
        <span className="text-ink-secondary text-xs font-normal hidden group-open:inline">Hide</span>
      </summary>
      <div className="space-y-5 border-t border-border-subtle p-5 bg-surface-muted/30">{children}</div>
    </details>
  );
}

export function KeyFindings({ findings }: { findings: string[] }) {
  if (!findings.length) return null;
  return (
    <Card>
      <Header icon={Lightbulb} title="Key findings" subtitle="The most important results for this sample." />
      <ul className="space-y-2">
        {findings.slice(0, 4).map((f) => (
          <li key={f} className="flex gap-2.5 text-sm text-ink leading-relaxed">
            <span className="mt-2 h-1.5 w-1.5 rounded-full bg-primary shrink-0" />
            <span>{f}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}

const PARTS: { key: ModalityName; label: string; short: string; icon: any; explains: string }[] = [
  { key: 'microscopy', label: 'Microscopy', short: 'Microscopy', icon: Microscope, explains: 'Are the bacteria clumped together like a biofilm?' },
  { key: 'spectroscopy', label: 'Raman spectroscopy', short: 'Raman', icon: Atom, explains: 'Is there a chemical signal of biofilm matrix?' },
  { key: 'genomics', label: 'Genomics', short: 'Genome', icon: Dna, explains: 'Does the genome carry biofilm genes?' },
  { key: 'clinical', label: 'Clinical risk factors', short: 'Clinical', icon: ClipboardList, explains: 'How many known risk factors are present?' },
];

export function ScoreBreakdown({ result }: { result: AnalysisResponse }) {
  const parts = result.scoreBreakdown ?? [];
  const score = result.prediction?.biofilmProbability ?? 0;
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>How the score was calculated</CardTitle>
          <p className="text-sm text-ink-secondary mt-0.5">
            Each type of evidence gives an indicator from 0% to 100%. The score is their average.
          </p>
        </div>
      </CardHeader>
      <div className="space-y-3">
        {PARTS.map((p) => {
          const part = parts.find((x) => x.modality === p.key);
          const provided = !!result.modalities?.[p.key]?.available || (p.key === 'clinical' && !!result.evidence?.clinical);
          const status = part ? pct(part.indicator) : provided ? 'Not assessed' : 'Not provided';
          return (
            <div key={p.key}>
              <div className="flex items-center justify-between gap-3 text-sm">
                <span className="inline-flex items-center gap-2 text-ink font-medium">
                  <p.icon className="h-4 w-4 text-primary" /> {p.label}
                </span>
                <span className={part ? 'font-mono text-ink' : 'text-ink-secondary text-[13px]'}>{status}</span>
              </div>
              <div className="mt-1.5 h-2 rounded-full bg-surface-muted overflow-hidden">
                {part && <div className="h-full rounded-full bg-primary" style={{ width: pct(part.indicator) }} />}
              </div>
              <p className="mt-1 text-[12px] text-ink-secondary">{p.explains}</p>
            </div>
          );
        })}
      </div>
      <div className="mt-4 pt-3 border-t border-border-subtle text-sm text-ink">
        Score = average of {parts.length} measured indicator{parts.length === 1 ? '' : 's'} ={' '}
        <span className="font-semibold">{pct(score)}</span>
      </div>
    </Card>
  );
}

export function EvidenceError({ title, message }: { title: string; message: string }) {
  return (
    <Card>
      <div className="flex gap-3">
        <AlertTriangle className="h-5 w-5 text-warning shrink-0" />
        <div>
          <p className="text-sm font-semibold text-ink">{title}</p>
          <p className="text-sm text-ink-secondary">{message}</p>
        </div>
      </div>
    </Card>
  );
}

// ── Per-modality cards ───────────────────────────────────────────────────

export function MicroscopyCard({ m }: { m: MicroscopyEvidence }) {
  const meaning = {
    dense_clusters: 'the bacteria are packed into large clusters, the typical structure of a biofilm.',
    micro_colonies: 'the bacteria are starting to form small groups, as in the early stage of a biofilm.',
    scattered: 'the bacteria are mostly separate single cells, which is typical of free-floating bacteria, not a biofilm.',
  }[m.pattern];
  return (
    <Card>
      <Header icon={Microscope} title="Microscopy image analysis" subtitle={`Measured from the uploaded image (${m.stain}).`} />
      <div className="grid sm:grid-cols-5 gap-4">
        <div className="sm:col-span-2">
          <img src={m.overlay_png} alt="Microscopy image with detected clusters outlined" className="w-full rounded-md border border-border" />
          <p className="mt-1.5 text-[11px] text-ink-secondary">
            <span className="inline-block h-2 w-2 bg-[#FFD600] mr-1" />Cluster
            <span className="inline-block h-2 w-2 bg-[#00DCFF] ml-3 mr-1" />Micro-colony
          </p>
        </div>
        <div className="sm:col-span-3 grid grid-cols-2 gap-3 content-start">
          <Stat label="Surface covered" value={`${m.coverage_pct}%`} hint="Share of the image covered by cells" />
          <Stat label="Cells in clusters" value={`${m.clustered_biomass_pct}%`} hint="Share of cells inside large clusters" />
          <Stat label="Clusters" value={m.cluster_count} hint={`${m.micro_colony_count} smaller micro-colonies`} />
          <Stat label="Largest cluster" value={`${m.largest_cluster_pct}%`} hint="Of the whole image" />
          {m.live_pct !== null && <Stat label="Live cells" value={`${m.live_pct}%`} hint="Green (live) vs red (dead) stain" />}
          {m.matrix_pct !== null && <Stat label="Matrix stain" value={`${m.matrix_pct}%`} hint="Blue biofilm matrix (EPS) signal" />}
        </div>
      </div>
      <p className="mt-4 text-sm font-medium text-ink">{m.pattern_text}.</p>
      <Meaning>{meaning}</Meaning>
    </Card>
  );
}

export function SpectrumCard({ s }: { s: SpectrumEvidence }) {
  const data = s.trace.map(([x, y]) => ({ x, y }));
  const quality = { good: 'success', fair: 'warning', poor: 'danger' }[s.quality] as any;
  return (
    <Card>
      <Header icon={Atom} title="Raman spectrum analysis" subtitle={`${s.range_cm[0]}–${s.range_cm[1]} cm⁻¹ · ${s.points} points, background removed.`} />
      <div className="h-56 -ml-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 10, right: 12, left: 0, bottom: 4 }}>
            <XAxis dataKey="x" type="number" domain={['dataMin', 'dataMax']} tick={{ fontSize: 11 }} tickCount={8}
              label={{ value: 'Raman shift (cm⁻¹)', position: 'insideBottom', offset: -2, fontSize: 11 }} height={36} />
            <YAxis tick={{ fontSize: 11 }} domain={[0, 1.05]} ticks={[0, 0.5, 1]} width={36} />
            <Tooltip formatter={(v: number) => v.toFixed(2)} labelFormatter={(l) => `${l} cm⁻¹`} />
            <Line type="monotone" dataKey="y" stroke="#1B6E8A" strokeWidth={1.5} dot={false} isAnimationActive={false} />
            {s.peaks.map((p) => (
              <ReferenceDot key={p.wavenumber} x={p.wavenumber} y={p.intensity} r={4} fill="#D99A2B" stroke="white" />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-3 grid grid-cols-2 sm:grid-cols-3 gap-3">
        <Stat label="Matrix band" value={s.matrix_ratio ?? '—'} hint="Polysaccharide ÷ protein band" />
        <Stat label="Matrix signal" value={<span className="capitalize">{s.matrix_level}</span>} />
        <Stat label="Signal quality" value={<Badge variant={quality} size="sm" dot>{s.quality}</Badge>} hint={`Signal-to-noise ${s.snr}`} />
      </div>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-[11px] uppercase tracking-wider text-ink-secondary border-b border-border-subtle">
              <th className="py-2 pr-3 font-semibold">Peak (cm⁻¹)</th>
              <th className="py-2 font-semibold">Chemical meaning</th>
            </tr>
          </thead>
          <tbody>
            {s.peaks.map((p) => (
              <tr key={p.wavenumber} className="border-b border-border-subtle/60 last:border-0">
                <td className="py-2 pr-3 font-mono text-ink">{p.wavenumber}</td>
                <td className="py-2 text-ink">{p.assignment}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <Meaning>
        a Raman spectrum is a chemical fingerprint. Biofilm bacteria make a sugar-based matrix (EPS), which shows up
        as a band near 1,100 cm⁻¹. {s.matrix_text}.
      </Meaning>
    </Card>
  );
}

export function GenomeCard({ g }: { g: GenomeEvidence }) {
  const model = g.genomic_model;
  return (
    <Card>
      <Header icon={Dna} title="Genome analysis" subtitle="Assembly statistics and a screen for resistance and biofilm genes." />
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <Stat label="Genome size" value={`${(g.length_bp / 1e6).toFixed(2)} Mb`} />
        <Stat label="GC content" value={`${g.gc_pct}%`} />
        <Stat label="Contigs" value={g.contigs} hint="Pieces in the assembly" />
        <Stat label="N50" value={`${(g.n50_bp / 1000).toFixed(0)} kb`} hint="Assembly quality (higher is better)" />
      </div>

      {g.markers.length > 0 && (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] uppercase tracking-wider text-ink-secondary border-b border-border-subtle">
                <th className="py-2 pr-3 font-semibold">Gene</th>
                <th className="py-2 pr-3 font-semibold">What it does</th>
                <th className="py-2 pr-3 font-semibold">Match</th>
                <th className="py-2 font-semibold">Result</th>
              </tr>
            </thead>
            <tbody>
              {g.markers.map((m) => (
                <tr key={m.gene} className="border-b border-border-subtle/60 last:border-0">
                  <td className="py-2 pr-3 font-mono italic text-ink">{m.gene}</td>
                  <td className="py-2 pr-3 text-ink">{m.role}</td>
                  <td className="py-2 pr-3 font-mono text-ink-secondary">{m.coverage_pct}%</td>
                  <td className="py-2">
                    {m.present ? (
                      <span className="inline-flex items-center gap-1 text-danger font-medium"><CheckCircle2 className="h-4 w-4" /> Found</span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-ink-secondary"><CircleSlash className="h-4 w-4" /> Not found</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-1.5 text-[11px] text-ink-secondary">
            A gene counts as found when at least 80% of its sequence fragments occur in the genome. Panel: staphylococcal genes from NCBI.
          </p>
        </div>
      )}

      <div className="mt-4 rounded-md border border-border-subtle p-3">
        <p className="text-sm font-medium text-ink">Trained genomic model (pathogenic vs commensal <i>S. epidermidis</i>)</p>
        {model.status === 'completed' ? (
          <p className="mt-1 text-sm text-ink">
            Predicted <b>{model.predicted_class}</b>, probability {Math.round((model.probability_pathogenic ?? 0) * 100)}%.
          </p>
        ) : (
          <p className="mt-1 text-sm text-ink-secondary">
            {model.status === 'out_of_scope'
              ? 'Not run: this genome is outside the model\'s training data (only S. epidermidis genomes).'
              : 'Not run: ' + (model.reasons ?? []).join('; ')}
          </p>
        )}
      </div>

      <Meaning>
        {g.mecA ? 'mecA was found, so this strain is expected to resist methicillin and similar antibiotics (MRSA/MRSE). ' : ''}
        {g.ica_operon
          ? 'The ica genes were found, so the bacterium can produce biofilm matrix.'
          : 'The ica biofilm genes were not found in this genome (the panel only covers staphylococci).'}
      </Meaning>
    </Card>
  );
}

export function ClinicalFactorsCard({ c }: { c: ClinicalEvidence }) {
  return (
    <Card>
      <Header icon={ClipboardList} title="Clinical risk factors" subtitle={`${c.present_count} of ${c.total} recognised biofilm risk factors present.`} />
      <ul className="space-y-2.5">
        {c.factors.map((f) => (
          <li key={f.factor} className="flex gap-3">
            {f.present ? (
              <CheckCircle2 className="h-5 w-5 text-warning shrink-0" />
            ) : (
              <CircleSlash className="h-5 w-5 text-ink-secondary/60 shrink-0" />
            )}
            <div>
              <p className={f.present ? 'text-sm font-medium text-ink' : 'text-sm text-ink-secondary'}>{f.factor}</p>
              <p className="text-[12px] text-ink-secondary">{f.why}</p>
            </div>
          </li>
        ))}
      </ul>
    </Card>
  );
}
