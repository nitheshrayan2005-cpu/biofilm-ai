'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { RadialBarChart, RadialBar, ResponsiveContainer, PolarAngleAxis } from 'recharts';
import {
  Download,
  FlaskConical,
  ArrowRight,
  ClipboardList,
  Microscope,
  Atom,
  Dna,
  ShieldCheck,
  RefreshCw,
} from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { StatusBanner } from '@/components/ui/Modal';
import { DemoBadge } from '@/components/ui/DemoBadge';
import { formatDateTime } from '@/lib/utils';
import { AnalysisResponse } from '@/lib/types';
import { getAnalysis } from '@/lib/api';
import { clinicalLabel, RISK_MEANING } from '@/lib/clinicalLabels';

export default function ResultsPage() {
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [requestInfo, setRequestInfo] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // /results?id=... shows that analysis (opened from History); plain /results
    // shows the last analysis run in this tab.
    const id = new URLSearchParams(window.location.search).get('id');
    let last: AnalysisResponse | null = null;
    try {
      const r = sessionStorage.getItem('biofilm-last-result');
      last = r ? JSON.parse(r) : null;
    } catch {}

    if (!id || last?.analysisId === id) {
      setResult(last);
      try {
        const ri = sessionStorage.getItem('biofilm-last-request');
        if (ri) setRequestInfo(JSON.parse(ri));
      } catch {}
      setLoading(false);
      return;
    }

    let cancelled = false;
    getAnalysis(id)
      .catch(() => null)
      .then((analysis) => {
        if (cancelled) return;
        if (analysis) {
          let ri: string | null = null;
          try {
            ri = localStorage.getItem(`biofilm-request-${id}`);
          } catch {}
          // The Download Report button reads the open analysis from session storage.
          try {
            sessionStorage.setItem('biofilm-last-result', JSON.stringify(analysis));
            if (ri) sessionStorage.setItem('biofilm-last-request', ri);
            else sessionStorage.removeItem('biofilm-last-request');
          } catch {}
          setResult(analysis);
          setRequestInfo(ri ? JSON.parse(ri) : null);
        }
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) return null;

  if (!result) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-20 text-center">
        <Card padding="lg">
          <div className="py-8">
            <div className="h-12 w-12 mx-auto rounded-lg bg-surface-muted text-ink-secondary flex items-center justify-center mb-4">
              <FlaskConical className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-semibold text-ink">No analysis result</h3>
            <p className="mt-2 text-sm text-ink-secondary">
              Run a multimodal analysis to see model output, modality evidence, and interpretation.
            </p>
            <Link href="/analyze">
              <Button className="mt-5" iconRight={<ArrowRight className="h-4 w-4" />}>
                Start Analysis
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
        <div>
          <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">Analysis Result</p>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-ink-secondary">
            <span className="font-mono">{result.analysisId}</span>
            {result.sampleId && (
              <>
                <span className="text-border">·</span>
                <span>Sample {result.sampleId}</span>
              </>
            )}
            <span className="text-border">·</span>
            <span>Generated {formatDateTime(result.completedAt || result.createdAt)}</span>
          </div>
        </div>
        <DemoBadge />
      </div>

      <div className="rise-in">
        <ResultHero result={result} />
      </div>

      <div className="mt-6 rise-in" style={{ animationDelay: '150ms' }}>
        <Disclaimer result={result} />
      </div>

      <div className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-2 space-y-5 rise-in" style={{ animationDelay: '300ms' }}>
          <ModalityEvidence result={result} />
        </div>
        <div className="space-y-5">
          <div className="rise-in" style={{ animationDelay: '400ms' }}>
            <ClinicalSummary requestInfo={requestInfo} />
          </div>
          <div className="rise-in" style={{ animationDelay: '500ms' }}>
            <Actions result={result} />
          </div>
        </div>
      </div>
    </div>
  );
}

function ResultHero({ result }: { result: AnalysisResponse }) {
  const probability = result.prediction?.biofilmProbability ?? 0;
  const category = result.prediction?.riskCategory ?? 'low';
  const pct = Math.round(probability * 100);
  const shown = useCountUp(pct);
  const color = category === 'high' ? '#C94C4C' : category === 'intermediate' ? '#D99A2B' : '#2E8B72';
  const accent =
    category === 'high' ? 'danger' : category === 'intermediate' ? 'warning' : 'success';

  const radialData = [
    { name: 'Probability', value: pct, fill: color },
  ];

  return (
    <div className="rounded-xl border border-border bg-white p-6 lg:p-8 shadow-card relative overflow-hidden">
      <div className="absolute -right-32 -top-32 h-72 w-72 rounded-full bg-primary-50 opacity-50 pointer-events-none" />
      <div className="grid lg:grid-cols-2 gap-8 items-center relative">
        <div>
          <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">Model output</p>
          <h2 className="mt-2 text-3xl font-semibold text-ink">Biofilm-Associated Risk</h2>
          <p className="mt-2 text-sm text-ink-secondary max-w-md">
            Combined estimate from the evidence supplied for this sample.
          </p>

          <div className="mt-5 flex flex-wrap items-center gap-2">
            <Badge variant={accent as any} size="md" dot className="pop-in" style={{ animationDelay: '900ms' }}>
              Risk category: {category}
            </Badge>
            <Badge variant="neutral" size="md">
              Model-estimated probability
            </Badge>
          </div>
          {RISK_MEANING[category] && (
            <p className="mt-4 text-sm text-ink leading-relaxed max-w-md rise-in" style={{ animationDelay: '1100ms' }}>
              {RISK_MEANING[category]}
            </p>
          )}
        </div>

        <div className="flex items-center justify-center">
          <div className="relative h-64 w-64">
            <div
              className="absolute inset-6 rounded-full blur-2xl result-glow pointer-events-none"
              style={{ backgroundColor: color }}
            />
            <ResponsiveContainer width="100%" height="100%">
              <RadialBarChart innerRadius="68%" outerRadius="100%" data={radialData} startAngle={90} endAngle={-270}>
                <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
                <RadialBar dataKey="value" cornerRadius={10} background={{ fill: '#F5FBFD' }} animationDuration={1400} animationEasing="ease-out" />
              </RadialBarChart>
            </ResponsiveContainer>
            <div className="absolute inset-[18%] rounded-full bg-white flex flex-col items-center justify-center text-center">
              <p className="text-5xl font-semibold leading-none tabular-nums" style={{ color }}>
                {shown}<span className="text-2xl align-top">%</span>
              </p>
              <p className="text-[11px] uppercase tracking-widest text-ink-secondary mt-2">Probability</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Disclaimer({ result }: { result: AnalysisResponse }) {
  const msg = result.message || 'This probability represents model output and should not be interpreted as a confirmed clinical diagnosis. Laboratory confirmation and professional clinical judgment remain necessary.';
  return (
    <div className="rounded-lg border border-warning-100 bg-warning-50/60 p-4 sm:p-5">
      <div className="flex gap-3">
        <div className="h-8 w-8 rounded-md bg-warning-100 text-warning flex items-center justify-center shrink-0">
          <ShieldCheck className="h-4 w-4" />
        </div>
        <div>
          <p className="text-sm font-semibold text-ink">Research prototype output</p>
          <p className="mt-1 text-[13px] text-ink-secondary leading-relaxed">{msg}</p>
          <div className="mt-2">
            <Badge variant="warning" size="sm" dot>
              {result.modelMode === 'demo' ? 'DEMO MODEL MODE' : 'Model mode: ' + result.modelMode}
            </Badge>
          </div>
        </div>
      </div>
    </div>
  );
}

function ModalityEvidence({ result }: { result: AnalysisResponse }) {
  const modalities = result.modalities;
  const items = [
    {
      key: 'microscopy',
      title: 'Microscopy',
      icon: Microscope,
      available: !!modalities?.microscopy?.available,
    },
    {
      key: 'spectroscopy',
      title: 'Spectroscopy',
      icon: Atom,
      available: !!modalities?.spectroscopy?.available,
    },
    {
      key: 'genomics',
      title: 'Genomics',
      icon: Dna,
      available: !!modalities?.genomics?.available,
    },
    {
      key: 'clinical',
      title: 'Clinical',
      icon: ClipboardList,
      available: !!modalities?.clinical?.available,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Evidence Used</CardTitle>
          <p className="text-sm text-ink-secondary mt-0.5">Which types of evidence were provided for this sample.</p>
        </div>
      </CardHeader>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {items.map((m, i) => (
          <div
            key={m.key}
            className="rounded-md border border-border-subtle bg-surface-muted/40 p-3 pop-in transition-shadow hover:shadow-soft"
            style={{ animationDelay: `${450 + i * 90}ms` }}
          >
            <div className="flex items-center justify-between mb-2">
              <m.icon className="h-4 w-4 text-primary" />
              <Badge variant={m.available ? 'success' : 'neutral'} size="sm" dot>
                {m.available ? 'Available' : 'Not provided'}
              </Badge>
            </div>
            <p className="text-sm font-medium text-ink">{m.title}</p>
            <p className="text-[11px] text-ink-secondary mt-0.5">
              {m.available ? 'Used in this analysis' : 'Not included in this analysis'}
            </p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function ClinicalSummary({ requestInfo }: { requestInfo: any }) {
  if (!requestInfo) return null;
  const c = requestInfo.clinicalData || {};
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Clinical Context</CardTitle>
          <p className="text-sm text-ink-secondary mt-0.5">Information entered for this sample.</p>
        </div>
      </CardHeader>
      <dl className="space-y-3 text-sm">
        <Row label="Infection context" value={clinicalLabel('infectionContext', c.infectionContext)} />
        <Row label="Implant present" value={c.implantPresent ? 'Yes' : 'No'} />
        <Row label="Sample site" value={c.sampleSite || '—'} />
        <Row label="Duration (days)" value={c.chronicityDays ?? 0} />
        <Row label="Previous treatment" value={clinicalLabel('previousTreatment', c.previousTreatment)} />
        <Row label="Previous culture" value={clinicalLabel('previousCulture', c.previousCulture)} />
      </dl>

      <div className="mt-4 pt-4 border-t border-border-subtle">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-secondary">Additional notes</p>
        <p className="text-sm text-ink mt-1 whitespace-pre-wrap">
          {c.additionalNotes || 'No additional notes provided.'}
        </p>
      </div>
    </Card>
  );
}

function Row({ label, value }: { label: string; value: any }) {
  return (
    <div className="flex items-start justify-between gap-3 py-1.5 border-b border-border-subtle last:border-0">
      <dt className="text-ink-secondary text-[13px]">{label}</dt>
      <dd className="text-ink text-[13px] font-medium text-right">{value}</dd>
    </div>
  );
}

function Actions({ result }: { result: AnalysisResponse }) {
  const handleDownload = () => {
    try {
      // run the download immediately on the user gesture (avoid
      // browser security restrictions when delayed)
      const mod = require("@/lib/downloadReport");
      mod.downloadAnalysisReport();
    } catch (e: any) {
      try {
        alert(
          "Download failed: " + (e?.message || "unknown error") +
          "\nPlease complete an analysis first."
        );
      } catch { /* ignore */ }
    }
  };
  return (
    <Card>
      <CardHeader>
        <CardTitle>Result Actions</CardTitle>
      </CardHeader>
      <div className="space-y-2.5">
        <Button
          fullWidth
          iconLeft={<Download className="h-4 w-4" />}
          onClick={handleDownload}
        >
          Download Report
        </Button>
        <Link href="/analyze" className="block">
          <Button fullWidth variant="outline" iconRight={<RefreshCw className="h-4 w-4" />}>New Analysis</Button>
        </Link>
        <Link href="/history" className="block">
          <Button fullWidth variant="ghost" iconRight={<ArrowRight className="h-4 w-4" />}>View History</Button>
        </Link>
      </div>
    </Card>
  );
}

// Count from 0 up to the target over `ms` milliseconds (ease-out).
function useCountUp(target: number, ms = 1400): number {
  const [value, setValue] = useState(0);
  useEffect(() => {
    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / ms);
      setValue(Math.round(target * (1 - Math.pow(1 - t, 3))));
      if (t < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, ms]);
  return value;
}
