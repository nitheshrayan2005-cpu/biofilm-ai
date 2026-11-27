'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  ArrowRight,
  ArrowLeft,
  Check,
  Microscope,
  Atom,
  Dna,
  ClipboardList,
  FlaskConical,
  Sparkles,
  Edit2,
  ShieldCheck,
  Eye,
  Layers,
  Cpu,
  Brain,
  Activity,
  CheckCircle2,
} from 'lucide-react';
import { Card, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input, Select, Textarea, Toggle } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { StepIndicator } from '@/components/ui/Progress';
import { StatusBanner } from '@/components/ui/Modal';
import { DemoBadge } from '@/components/ui/DemoBadge';
import { FileUpload } from '@/components/analyze/FileUpload';
import { useAnalyze, STEPS } from '@/components/AnalyzeContext';
import { analyze } from '@/lib/api';
import { cn } from '@/lib/utils';

export default function AnalyzePage() {
  const router = useRouter();
  const { state, setStep, setSampleInfo } = useAnalyze();
  const [submitting, setSubmitting] = useState(false);

  const step = state.step;

  function next() {
    if (step < STEPS.length - 1) {
      setStep(Math.min(step + 1, STEPS.length - 1));
      if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }
  function prev() {
    if (step > 0) {
      setStep(Math.max(step - 1, 0));
      if (typeof window !== 'undefined') window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }

  async function runAnalysis() {
    setSubmitting(true);
    try {
      const [result] = await Promise.all([
        analyze({
          sampleInfo: state.sampleInfo,
          clinicalData: state.clinicalData,
          microscopyFile: state.microscopyFile ?? undefined,
          spectroscopyFile: state.spectroscopyFile ?? undefined,
          genomicsFile: state.genomicsFile ?? undefined,
        }),
        new Promise((resolve) => setTimeout(resolve, MIN_ANALYSIS_MS)),
      ]);
      const requestInfo = JSON.stringify({
        sampleInfo: state.sampleInfo,
        clinicalData: state.clinicalData,
      });
      sessionStorage.setItem('biofilm-last-result', JSON.stringify(result));
      sessionStorage.setItem('biofilm-last-request', requestInfo);
      // The backend does not return the clinical form, so keep it for reopening from History.
      try {
        localStorage.setItem(`biofilm-request-${result.analysisId}`, requestInfo);
      } catch {}
      router.push(`/results?id=${encodeURIComponent(result.analysisId)}`);
    } catch (err) {
      alert('AI analysis is temporarily unavailable. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3 mb-6">
        <div>
          <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">New Analysis</p>
          <h1 className="mt-2 text-2xl sm:text-3xl font-semibold text-ink">New Multimodal Analysis</h1>
          <p className="mt-1.5 text-sm text-ink-secondary">
            Provide the available sample information for research-oriented biofilm risk assessment.
          </p>
        </div>
        <DemoBadge />
      </div>

      <div className="rounded-lg border border-border bg-white p-4 sm:p-5 mb-6">
        <StepIndicator steps={STEPS} current={step} completed={step} />
      </div>

      <Card padding="lg" className="overflow-hidden">
        <div key={step} className="step-enter">
        {step === 0 && <SampleInfoStep form={state.sampleInfo} onChange={setSampleInfo} />}
        {step === 1 && <MicroscopyStep />}
        {step === 2 && <SpectroscopyStep />}
        {step === 3 && <GenomicsStep />}
        {step === 4 && <ClinicalDataStep />}
        {step === 5 && <ReviewStep onRun={runAnalysis} submitting={submitting} />}
        </div>
      </Card>

      <div className="mt-6 flex items-center justify-between">
        <Button
          variant="outline"
          iconLeft={<ArrowLeft className="h-4 w-4" />}
          onClick={prev}
          disabled={step === 0}
        >
          Back
        </Button>
        {step < STEPS.length - 1 ? (
          <Button
            onClick={next}
            iconRight={<ArrowRight className="h-4 w-4" />}
          >
            Continue
          </Button>
        ) : (
          <span className="text-xs text-ink-secondary">Use "Run Multimodal Analysis" above</span>
        )}
      </div>

      <ProcessingOverlay submitting={submitting} />
    </div>
  );
}

// Minimum time the "Analysing sample" screen stays up, so the pipeline is visible.
const MIN_ANALYSIS_MS = 4000;

const PIPELINE = [
  { id: 'validate', label: 'Validating input', icon: CheckCircle2 },
  { id: 'micro', label: 'Scanning microscopy image', icon: Microscope },
  { id: 'spectro', label: 'Reading Raman spectrum', icon: Atom },
  { id: 'gen', label: 'Processing genome sequence', icon: Dna },
  { id: 'clinic', label: 'Encoding clinical information', icon: ClipboardList },
  { id: 'fuse', label: 'Combining all evidence', icon: Brain },
  { id: 'predict', label: 'Estimating biofilm risk', icon: Activity },
  { id: 'interpret', label: 'Preparing results', icon: Eye },
];

function ProcessingOverlay({ submitting }: { submitting: boolean }) {
  const { state } = useAnalyze();
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    if (!submitting) {
      setActiveStep(0);
      return;
    }
    const interval = setInterval(() => {
      setActiveStep((active) => (active < PIPELINE.length - 1 ? active + 1 : active));
    }, MIN_ANALYSIS_MS / PIPELINE.length);
    return () => clearInterval(interval);
  }, [submitting]);

  if (!submitting) return null;

  const pct = Math.round(((activeStep + 1) / PIPELINE.length) * 100);
  const stageClass = (step: number) =>
    cn(
      'rounded-lg border p-3 transition-all duration-500',
      activeStep === step
        ? 'border-secondary-300/80 bg-white/10 shadow-[0_0_24px_rgba(42,157,143,0.35)]'
        : 'border-white/10 bg-white/5'
    );

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Analysis in progress"
      className="fixed inset-0 z-50 bg-navy-900/60 backdrop-blur-md flex items-center justify-center p-4 animate-fade-in"
    >
      <div className="w-full max-w-3xl rounded-2xl overflow-hidden shadow-lifted border border-white/10 grid md:grid-cols-2 pop-in">
        {/* Visual stage */}
        <div className="bg-gradient-to-br from-navy-800 via-navy-700 to-primary-800 p-5 space-y-3 text-white">
          <div className={stageClass(1)}>
            <StageLabel icon={Microscope} label="Microscopy" skipped={!state.microscopyFile} />
            <div className="relative mt-2 h-28 rounded-md overflow-hidden bg-black/40">
              {state.microscopyPreview ? (
                <img src={state.microscopyPreview} alt="" className="h-full w-full object-cover opacity-90" />
              ) : (
                <div className="h-full w-full diagram-grid opacity-20" />
              )}
              {state.microscopyFile && <div className="scan-line" />}
            </div>
          </div>

          <div className={stageClass(2)}>
            <StageLabel icon={Atom} label="Raman spectrum" skipped={!state.spectroscopyFile} />
            <svg viewBox="0 0 300 70" className="mt-2 h-16 w-full" preserveAspectRatio="none">
              <path
                d={spectrumPath(state.spectroscopyPreview)}
                pathLength={1}
                className={state.spectroscopyFile ? 'draw-line-loop' : ''}
                fill="none"
                stroke="#7AC6D9"
                strokeWidth="2"
                strokeDasharray="1"
                strokeDashoffset={state.spectroscopyFile ? undefined : 0}
                opacity={state.spectroscopyFile ? 1 : 0.25}
              />
            </svg>
          </div>

          <div className={stageClass(3)}>
            <StageLabel icon={Dna} label="Genome" skipped={!state.genomicsFile} />
            <div className={cn('mt-2 h-14 flex items-center justify-between px-2', !state.genomicsFile && 'opacity-25')}>
              {Array.from({ length: 14 }).map((_, i) => (
                <div key={i} className="relative h-full w-2 flex items-center justify-center">
                  <span
                    className={cn('absolute h-2 w-2 rounded-full bg-secondary-300', state.genomicsFile && 'helix-dot')}
                    style={{ animationDelay: `${i * -0.12}s` }}
                  />
                  <span
                    className={cn('absolute h-2 w-2 rounded-full bg-primary-300', state.genomicsFile && 'helix-dot b')}
                    style={{ animationDelay: `${i * -0.12}s` }}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Progress */}
        <div className="bg-white p-6 sm:p-7 flex flex-col">
          <div className="flex items-center gap-3">
            <div className="relative h-10 w-10 rounded-full bg-primary-50 text-primary flex items-center justify-center ring-pulse">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">Multimodal pipeline</p>
              <h3 className="text-base font-semibold text-ink">
                Analysing {state.sampleInfo.sampleId || 'sample'}
              </h3>
            </div>
          </div>

          <div className="mt-5">
            <div className="flex items-center justify-between text-[12px] text-ink-secondary mb-1.5">
              <span>{PIPELINE[activeStep].label}…</span>
              <span className="font-mono font-semibold text-primary">{pct}%</span>
            </div>
            <div className="h-2 rounded-full bg-border-subtle overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-primary via-secondary to-primary-300 transition-all duration-500 ease-out"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>

          <ul className="mt-5 space-y-1.5 flex-1">
            {PIPELINE.map((s, i) => {
              const completed = i < activeStep;
              const active = i === activeStep;
              return (
                <li
                  key={s.id}
                  className={cn(
                    'flex items-center gap-3 rounded-md px-2.5 py-1.5 transition-colors duration-300',
                    active && 'bg-primary-50'
                  )}
                >
                  <div
                    className={cn(
                      'h-5 w-5 rounded-full flex items-center justify-center shrink-0 transition-colors duration-300',
                      completed && 'bg-success text-white',
                      active && 'bg-primary text-white',
                      !completed && !active && 'bg-border'
                    )}
                  >
                    {completed ? (
                      <Check className="h-3 w-3 pop-in" strokeWidth={3} />
                    ) : active ? (
                      <span className="h-1.5 w-1.5 rounded-full bg-white animate-pulse-soft" />
                    ) : null}
                  </div>
                  <span
                    className={cn(
                      'text-[13px]',
                      completed && 'text-success-700',
                      active && 'text-primary-700 font-medium',
                      !completed && !active && 'text-ink-secondary'
                    )}
                  >
                    {s.label}
                  </span>
                </li>
              );
            })}
          </ul>

          <div className="mt-4 pt-4 border-t border-border-subtle">
            <DemoBadge small />
          </div>
        </div>
      </div>
    </div>
  );
}

function StageLabel({ icon: Icon, label, skipped }: { icon: any; label: string; skipped: boolean }) {
  return (
    <div className="flex items-center justify-between text-[11px] uppercase tracking-wider">
      <span className="flex items-center gap-1.5 font-semibold text-white/90">
        <Icon className="h-3.5 w-3.5" /> {label}
      </span>
      <span className={skipped ? 'text-white/40' : 'text-secondary-200'}>{skipped ? 'Not provided' : 'Processing'}</span>
    </div>
  );
}

// SVG path for the spectrum tile: the uploaded spectrum if available, otherwise
// a generic peak shape.
function spectrumPath(points: { wavelength: number; intensity: number }[] | null): string {
  const ys = points && points.length > 5
    ? points.map((p) => p.intensity)
    : Array.from({ length: 120 }, (_, i) =>
        Math.exp(-((i - 25) ** 2) / 18) + 1.4 * Math.exp(-((i - 55) ** 2) / 12) +
        0.8 * Math.exp(-((i - 78) ** 2) / 30) + 1.2 * Math.exp(-((i - 100) ** 2) / 20));
  const min = Math.min(...ys);
  const range = Math.max(...ys) - min || 1;
  return ys
    .map((v, i) => `${i === 0 ? 'M' : 'L'}${((i / (ys.length - 1)) * 300).toFixed(1)},${(64 - ((v - min) / range) * 58).toFixed(1)}`)
    .join(' ');
}

// ----- Step 1: Sample Info -----
function SampleInfoStep({
  form,
  onChange,
}: {
  form: any;
  onChange: (v: any) => void;
}) {
  return (
    <div className="animate-fade-in">
      <StepHeader
        eyebrow="Step 1"
        title="Sample information"
        description="Provide identifiers and high-level context for this multimodal analysis."
      />

      <div className="grid sm:grid-cols-2 gap-4 mb-5">
        <Input
          label="Sample ID"
          placeholder="e.g. S-01842"
          value={form.sampleId}
          onChange={(e) => onChange({ ...form, sampleId: e.target.value })}
          required
        />
        <Input
          label="Study ID"
          placeholder="e.g. BF-LONG-2026"
          value={form.studyId}
          onChange={(e) => onChange({ ...form, studyId: e.target.value })}
          required
        />
        <Select
          label="Sample Type"
          options={[
            { value: '', label: 'Select type…' },
            { value: 'Wound swab', label: 'Wound swab' },
            { value: 'Implant sonicate', label: 'Implant sonicate' },
            { value: 'Tissue biopsy', label: 'Tissue biopsy' },
            { value: 'Sputum', label: 'Sputum' },
            { value: 'Blood culture', label: 'Blood culture' },
            { value: 'Urine sample', label: 'Urine sample' },
          ]}
          value={form.sampleType}
          onChange={(e) => onChange({ ...form, sampleType: e.target.value })}
          required
        />
        <Input
          label="Collection date"
          type="date"
          value={form.collectionDate}
          onChange={(e) => onChange({ ...form, collectionDate: e.target.value })}
        />
        <Select
          label="Infection context"
          options={[
            { value: '', label: 'Select…' },
            { value: 'Chronic wound', label: 'Chronic wound' },
            { value: 'Orthopedic implant', label: 'Orthopedic implant' },
            { value: 'Catheter-associated', label: 'Catheter-associated' },
            { value: 'Post-surgical', label: 'Post-surgical' },
            { value: 'Burn wound', label: 'Burn wound' },
            { value: 'Periodontal', label: 'Periodontal' },
          ]}
          value={form.infectionContext}
          onChange={(e) => onChange({ ...form, infectionContext: e.target.value })}
        />
        <Input
          label="Wound / implant context"
          placeholder="e.g. Knee prosthesis / chronic ulcer"
          value={form.woundOrImplant}
          onChange={(e) => onChange({ ...form, woundOrImplant: e.target.value })}
        />
      </div>

      <Textarea
        label="Notes"
        placeholder="Free-text research notes…"
        value={form.notes}
        onChange={(e) => onChange({ ...form, notes: e.target.value })}
        rows={3}
      />

      <div className="mt-5">
        <StatusBanner
          variant="info"
          icon={<ShieldCheck className="h-4 w-4" />}
          description="Use research/sample identifiers instead of patient names or directly identifying information."
        />
      </div>
    </div>
  );
}

// ----- Step 2: Microscopy -----
function MicroscopyStep() {
  const { state, setMicroscopyFile } = useAnalyze();
  return (
    <div className="animate-fade-in">
      <StepHeader
        eyebrow="Step 2"
        title="Microscopy image"
        description="Upload a microscopy image associated with the sample. Supported formats include PNG, JPG, JPEG, and TIFF."
      />

      <FileUpload
        title=""
        icon="image"
        accept="image/*,.tif,.tiff"
        examples={['PNG', 'JPG', 'JPEG', 'TIFF']}
        maxSizeMB={50}
        file={state.microscopyFile}
        onFile={setMicroscopyFile}
      />

      <div className="mt-6">
        <DemoBadge small />
        <p className="mt-2 text-xs text-ink-secondary leading-relaxed">
          The image will be encoded by the Vision Encoder once submitted. Until the multimodal
          model is connected, no actual visual analysis is performed on the uploaded file.
        </p>
      </div>
    </div>
  );
}

// ----- Step 3: Spectroscopy -----
function SpectroscopyStep() {
  const { state, setSpectroscopyFile } = useAnalyze();

  function handle(f: File | null, _preview?: string | null) {
    if (!f) return setSpectroscopyFile(null, null);

    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      const lines = text.split(/\r?\n/).filter(Boolean).slice(0, 200);
      const points = lines
        .map((line) => {
          const m = line.split(/[,;\s\t]+/).slice(0, 2).map(Number);
          if (!isFinite(m[0]) || !isFinite(m[1])) return null;
          return { wavelength: m[0], intensity: m[1] };
        })
        .filter(Boolean);
      setSpectroscopyFile(f, points && points.length > 0 ? points : null);
    };
    reader.readAsText(f);
  }

  return (
    <div className="animate-fade-in">
      <StepHeader
        eyebrow="Step 3"
        title="Spectroscopy data"
        description="Provide tabular spectroscopy data such as wavelength/intensity or wavenumber/absorbance."
      />

      <FileUpload
        title=""
        icon="chart"
        accept=".csv,.txt,.xlsx,text/*,application/vnd.ms-excel"
        examples={['CSV', 'TXT', 'XLSX']}
        maxSizeMB={20}
        file={state.spectroscopyFile}
        onFile={handle}
      />

      {state.spectroscopyPreview && state.spectroscopyPreview.length > 0 && (
        <div className="mt-6">
          <p className="text-sm font-medium text-ink mb-2">Preview from uploaded data</p>
          <div className="rounded-lg border border-border bg-white p-4 h-56">
            <SpectroscopyPreview data={state.spectroscopyPreview} />
          </div>
          <p className="mt-2 text-[11px] text-ink-secondary">
            {state.spectroscopyPreview.length} data points detected. Ready for spectral encoding.
          </p>
        </div>
      )}
    </div>
  );
}

function SpectroscopyPreview({ data }: { data: { wavelength: number; intensity: number }[] }) {
  const max = Math.max(...data.map((d) => d.intensity));
  const min = Math.min(...data.map((d) => d.intensity));
  const range = max - min || 1;

  return (
    <svg viewBox={`0 0 ${data.length * 4} 100`} className="w-full h-full" preserveAspectRatio="none">
      <polyline
        key={data.length + ':' + data[0]?.intensity}
        className="draw-line"
        pathLength={1}
        fill="none"
        stroke="#176B87"
        strokeWidth="1.5"
        points={data
          .map((d, i) => `${i * 4},${100 - ((d.intensity - min) / range) * 90 - 5}`)
          .join(' ')}
      />
    </svg>
  );
}

// ----- Step 4: Genomics -----
function GenomicsStep() {
  const { state, setGenomicsFile } = useAnalyze();

  function detectFormat(name: string): 'fasta' | 'csv' | 'txt' | 'unknown' {
    const ext = name.split('.').pop()?.toLowerCase();
    if (ext === 'fasta' || ext === 'fa' || ext === 'fna') return 'fasta';
    if (ext === 'csv') return 'csv';
    if (ext === 'txt') return 'txt';
    return 'unknown';
  }

  function handle(f: File | null, _p?: string | null) {
    if (!f) return setGenomicsFile(null, null, null);

    const fmt = detectFormat(f.name);
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      let featureCount = 0;
      let sequenceLength = 0;
      if (fmt === 'fasta') {
        const lines = text.split('\n');
        sequenceLength = lines.filter((l) => !l.startsWith('>')).join('').length;
      } else {
        featureCount = text.split(/\n|[,;\s\t]+/).filter(Boolean).length;
      }
      setGenomicsFile(f, `${f.name} · ${fmt.toUpperCase()}${fmt === 'fasta' ? ` · ${sequenceLength} bp` : ` · ${featureCount} tokens`}`, fmt);
    };
    reader.readAsText(f.slice(0, 4096));
  }

  return (
    <div className="animate-fade-in">
      <StepHeader
        eyebrow="Step 4"
        title="Genomic data"
        description="Upload genomic data in CSV, TXT, or FASTA format. If the model supports missing modalities, this step can be skipped."
      />

      <FileUpload
        title=""
        icon="dna"
        accept=".csv,.txt,.fasta,.fa,.fna"
        examples={['CSV', 'TXT', 'FASTA']}
        maxSizeMB={20}
        file={state.genomicsFile}
        onFile={handle}
      />

      {state.genomicsFileName && (
        <div className="mt-5 rounded-lg border border-border bg-surface-muted p-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <KV label="File" value={state.genomicsFile?.name ?? '—'} />
          <KV label="Format" value={state.genomicsFormat?.toUpperCase() ?? '—'} />
          <KV
            label="Detected content"
            value={state.genomicsFileName.split(' · ').slice(2).join(' · ') || 'Loading preview…'}
          />
        </div>
      )}

      <div className="mt-6">
        <StatusBanner
          variant="neutral"
          icon={<FlaskConical className="h-4 w-4" />}
          description="Genomic features are encoded by the Genomic Encoder. The platform does not interpret or report specific genomic findings until connected to the production model."
        />
      </div>
    </div>
  );
}

// ----- Step 5: Clinical Data -----
function ClinicalDataStep() {
  const { state, setClinicalData } = useAnalyze();
  const data = state.clinicalData;

  return (
    <div className="animate-fade-in">
      <StepHeader
        eyebrow="Step 5"
        title="Clinical data"
        description="Provide structured research and clinical metadata for the multimodal encoder."
      />

      <div className="grid sm:grid-cols-2 gap-4">
        <Select
          label="Infection context"
          options={[
            { value: '', label: 'Select…' },
            { value: 'chronic-wound', label: 'Chronic wound' },
            { value: 'orthopedic-implant', label: 'Orthopedic implant' },
            { value: 'catheter', label: 'Catheter-associated' },
            { value: 'post-surgical', label: 'Post-surgical' },
          ]}
          value={data.infectionContext}
          onChange={(e) => setClinicalData({ ...data, infectionContext: e.target.value })}
        />
        <Input
          label="Chronicity / duration (days)"
          type="number"
          min={0}
          max={3650}
          value={data.chronicityDays}
          onChange={(e) => setClinicalData({ ...data, chronicityDays: Number(e.target.value) })}
        />
        <Select
          label="Implant present"
          options={[
            { value: 'no', label: 'No' },
            { value: 'yes', label: 'Yes' },
          ]}
          value={data.implantPresent ? 'yes' : 'no'}
          onChange={(e) => setClinicalData({ ...data, implantPresent: e.target.value === 'yes' })}
        />
        <Select
          label="Sample site"
          options={[
            { value: '', label: 'Select…' },
            { value: 'Abdomen', label: 'Abdomen' },
            { value: 'Knee (prosthetic)', label: 'Knee (prosthetic)' },
            { value: 'Lower leg', label: 'Lower leg' },
            { value: 'Forearm', label: 'Forearm' },
            { value: 'Hip', label: 'Hip' },
            { value: 'Mandible', label: 'Mandible' },
          ]}
          value={data.sampleSite}
          onChange={(e) => setClinicalData({ ...data, sampleSite: e.target.value })}
        />
        <Select
          label="Previous treatment category"
          options={[
            { value: '', label: 'Select…' },
            { value: 'none', label: 'None' },
            { value: 'antibiotics', label: 'Antibiotics' },
            { value: 'surgical-debridement', label: 'Surgical debridement' },
            { value: 'combination', label: 'Combination' },
          ]}
          value={data.previousTreatment}
          onChange={(e) => setClinicalData({ ...data, previousTreatment: e.target.value })}
        />
        <Select
          label="Previous culture information"
          options={[
            { value: '', label: 'Select…' },
            { value: 'negative', label: 'Negative' },
            { value: 'positive-mixed', label: 'Positive (mixed flora)' },
            { value: 'positive-pure', label: 'Positive (pure culture)' },
            { value: 'unknown', label: 'Unknown' },
          ]}
          value={data.previousCulture}
          onChange={(e) => setClinicalData({ ...data, previousCulture: e.target.value })}
        />
      </div>

      <div className="mt-4">
        <Textarea
          label="Additional notes"
          placeholder="e.g. relevant comorbidities, sampling technique…"
          value={data.additionalNotes}
          onChange={(e) => setClinicalData({ ...data, additionalNotes: e.target.value })}
          rows={3}
        />
      </div>

      <div className="mt-5">
        <StatusBanner
          variant="info"
          icon={<ShieldCheck className="h-4 w-4" />}
          description="Enter only the minimum information required for the research workflow. Avoid directly identifying patient information."
        />
      </div>
    </div>
  );
}

// ----- Step 6: Review -----
function ReviewStep({ onRun, submitting }: { onRun: () => void; submitting: boolean }) {
  const { state, setStep } = useAnalyze();

  const sections = [
    {
      id: 0,
      title: 'Sample Information',
      icon: ClipboardList,
      complete: !!state.sampleInfo.sampleId && !!state.sampleInfo.sampleType,
    },
    { id: 1, title: 'Microscopy', icon: Microscope, complete: !!state.microscopyFile },
    { id: 2, title: 'Spectroscopy', icon: Atom, complete: !!state.spectroscopyFile },
    { id: 3, title: 'Genomics', icon: Dna, complete: !!state.genomicsFile },
    {
      id: 4,
      title: 'Clinical Data',
      icon: ClipboardList,
      complete: !!state.clinicalData.infectionContext || !!state.clinicalData.sampleSite,
    },
  ];

  return (
    <div className="animate-fade-in">
      <StepHeader
        eyebrow="Step 6"
        title="Review sample"
        description="Confirm the information below before running the multimodal analysis."
      />

      <div className="space-y-3">
        {sections.map((sec) => (
          <div
            key={sec.id}
            className="flex items-center justify-between rounded-md border border-border bg-surface-muted/40 px-4 py-3"
          >
            <div className="flex items-center gap-3">
              <div
                className={`h-7 w-7 rounded-md flex items-center justify-center ${
                  sec.complete ? 'bg-success-50 text-success' : 'bg-warning-50 text-warning'
                }`}
              >
                {sec.complete ? <Check className="h-4 w-4" /> : <sec.icon className="h-3.5 w-3.5" />}
              </div>
              <div>
                <p className="text-sm font-medium text-ink">{sec.title}</p>
                <p className="text-xs text-ink-secondary">
                  {sec.complete ? 'Complete' : 'Available data not provided'}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={sec.complete ? 'success' : 'neutral'} size="sm" dot>
                {sec.complete ? 'Ready' : 'Optional'}
              </Badge>
              <button
                onClick={() => setStep(sec.id)}
                className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:text-primary-700"
              >
                <Edit2 className="h-3 w-3" /> Edit
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6">
        <StatusBanner
          variant="warning"
          icon={<FlaskConical className="h-4 w-4" />}
          title="Demo mode"
          description="The multimodal Transformer backend is not connected in this build. The result below will be a clearly labeled demo prediction."
        />
      </div>

      <div className="mt-7 flex flex-wrap items-center gap-3">
        <Button
          size="lg"
          onClick={onRun}
          loading={submitting}
          iconLeft={<Sparkles className="h-4 w-4" />}
        >
          Run Multimodal Analysis
        </Button>
      </div>
    </div>
  );
}

function StepHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow: string;
  title: string;
  description: string;
}) {
  return (
    <div className="mb-5 pb-5 border-b border-border-subtle">
      <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">{eyebrow}</p>
      <h2 className="mt-2 text-xl font-semibold text-ink">{title}</h2>
      <p className="mt-1.5 text-sm text-ink-secondary max-w-2xl">{description}</p>
    </div>
  );
}

function KV({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[11px] font-medium text-ink-secondary uppercase tracking-wider">{label}</p>
      <p className="text-sm text-ink mt-1 font-mono break-words">{value}</p>
    </div>
  );
}
