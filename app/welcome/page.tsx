import Link from 'next/link';
import {
  Microscope,
  Atom,
  Dna,
  ClipboardList,
  ArrowRight,
  Brain,
  Eye,
  Layers,
  ShieldCheck,
  Cpu,
  FlaskConical,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { HeroVisualization } from '@/components/landing/HeroVisualization';

const capabilities = [
  {
    icon: Microscope,
    title: 'Microscopy',
    body:
      'Confocal / SEM images reveal microbial colonies, aggregate structure, and the EPS matrix that characterizes biofilms.',
    tag: 'Vision Encoder',
  },
  {
    icon: Atom,
    title: 'Spectroscopy',
    body:
      'Raman / FTIR spectra capture biochemical signatures of pathogens, such as protein, nucleic acid, and polysaccharide bands.',
    tag: 'Spectral Encoder',
  },
  {
    icon: Dna,
    title: 'Genomics',
    body:
      'Genomic sequences (16S rRNA / whole genome) identify pathogen species and antimicrobial resistance genes.',
    tag: 'Genomic Encoder',
  },
  {
    icon: ClipboardList,
    title: 'Clinical Data',
    body:
      'Wound or implant context, infection duration, prior treatment, and culture results add patient-specific context.',
    tag: 'Clinical Encoder',
  },
];

const pipeline = [
  { id: 'encoders', label: 'Modal Encoders', sub: 'Vision · Spectral · Genomic · Clinical', icon: Cpu },
  { id: 'fusion', label: 'Cross-Attention Fusion', sub: 'Learns inter-modal relationships', icon: Layers },
  { id: 'unified', label: 'Unified Representation', sub: 'Joint multimodal embedding', icon: Brain },
  { id: 'head', label: 'Prediction Head', sub: 'Biofilm-associated probability', icon: Eye },
  { id: 'interpret', label: 'Research Interpretation', sub: 'Attention + contribution views', icon: ShieldCheck },
];

export default function LandingPage() {
  return (
    <div>
      <HeroSection />
      <CapabilitiesSection />
      <ArchitectureSection pipeline={pipeline} />
      <MetricsSection />
      <PrivacySection />
      <CTASection />
    </div>
  );
}

function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      <div className="absolute inset-0 diagram-grid opacity-30 pointer-events-none" />
      <div className="absolute top-0 left-0 right-0 h-[480px] bg-gradient-to-b from-primary-50/70 via-surface-muted to-transparent pointer-events-none" />

      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-12 pb-16 sm:pt-16 sm:pb-24 relative">
        <div className="grid lg:grid-cols-12 gap-10 lg:gap-12 items-center">
          <div className="lg:col-span-6 max-w-2xl">
            <span className="inline-flex items-center gap-2 rounded-full border border-primary-100 bg-primary-50 px-3 py-1 text-[11px] font-medium tracking-wider uppercase text-primary-700 animate-fade-in">
              <span className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse-soft" />
              Multimodal biomedical AI
            </span>
            <h1 className="mt-6 text-4xl sm:text-5xl lg:text-[56px] leading-[1.05] tracking-tight font-semibold text-ink text-balance animate-slide-up">
              Rapid detection of{' '}
              <span className="gradient-text">biofilm-forming pathogens</span>
            </h1>
            <p className="mt-6 text-[17px] leading-relaxed text-ink-secondary max-w-xl text-balance">
              A multi-modal transformer framework integrating microscopy, spectroscopy, genomics, and clinical data with cross-attention fusion for chronic wound and implant infection.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link href="/analyze">
                <Button size="lg" iconRight={<ArrowRight className="h-4 w-4" />} iconLeft={<FlaskConical className="h-4 w-4" />}>
                  Start Analysis
                </Button>
              </Link>
            </div>
          </div>

          <div className="lg:col-span-6 relative">
            <HeroVisualization />
            <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 inline-flex items-center gap-2 rounded-full bg-white border border-border px-3 py-1.5 shadow-card text-[11px] text-ink-secondary">
              <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse-soft" />
              Four modalities · one model · one prediction
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function CapabilitiesSection() {
  return (
    <section className="py-20 sm:py-24 bg-white border-y border-border-subtle">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">
            Multimodal data sources
          </p>
          <h2 className="mt-3 text-3xl sm:text-4xl font-semibold tracking-tight text-ink text-balance">
            Four Sources. One Integrated View.
          </h2>
          <p className="mt-4 text-base text-ink-secondary">
            Each modality contributes a learned representation. Cross-attention then fuses
            them into a single, model-interpretable prediction.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {capabilities.map((cap, i) => (
            <Card key={cap.title} className="relative hover:shadow-lifted transition-shadow duration-300 group">
              <div className="h-11 w-11 rounded-lg bg-primary-50 text-primary flex items-center justify-center mb-4 group-hover:bg-primary group-hover:text-white transition-colors">
                <cap.icon className="h-5 w-5" strokeWidth={1.8} />
              </div>
              <h3 className="text-base font-semibold text-ink">{cap.title}</h3>
              <p className="mt-2 text-sm text-ink-secondary leading-relaxed">{cap.body}</p>
              <div className="mt-4 pt-4 border-t border-border-subtle flex items-center justify-between">
                <span className="text-[11px] text-ink-secondary uppercase tracking-wider">{cap.tag}</span>
                <span className="text-[11px] text-ink-secondary font-mono">0{i + 1}</span>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

function ArchitectureSection({ pipeline }: { pipeline: { id: string; label: string; sub: string; icon: any }[] }) {
  return (
    <section className="py-20 sm:py-24 bg-surface-muted">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-12 gap-10 items-start">
          <div className="lg:col-span-5 lg:sticky lg:top-24">
            <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">
              Architecture
            </p>
            <h2 className="mt-3 text-3xl sm:text-4xl font-semibold tracking-tight text-ink text-balance">
              How BiofilmAI works
            </h2>
            <p className="mt-4 text-base text-ink-secondary leading-relaxed">
              Each modality is first converted into a learned representation. Cross-attention then
              enables the model to learn relationships between modalities before producing a unified
              representation for downstream prediction.
            </p>
            <div className="mt-6 space-y-3">
              {pipeline.map((step: any, i: number) => (
                <div key={step.id} className="flex items-start gap-3">
                  <div className="h-7 w-7 rounded-md bg-white border border-border text-primary flex items-center justify-center shrink-0 mt-0.5">
                    <step.icon className="h-3.5 w-3.5" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-baseline justify-between">
                      <p className="text-sm font-medium text-ink">{step.label}</p>
                      <span className="text-[11px] text-ink-secondary font-mono">Step 0{i + 1}</span>
                    </div>
                    <p className="text-[13px] text-ink-secondary">{step.sub}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="lg:col-span-7">
            <Card padding="lg" className="bg-white">
              <div className="text-xs uppercase tracking-wider font-semibold text-ink-secondary mb-4">
                Multimodal Transformer
              </div>
              <ArchitectureDiagram />
            </Card>
          </div>
        </div>
      </div>
    </section>
  );
}

function ArchitectureDiagram() {
  return (
    <div className="relative">
      <svg viewBox="0 0 500 460" className="w-full h-auto" aria-label="Detailed architecture diagram">
        <defs>
          <marker id="arrow2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#176B87" opacity="0.6" />
          </marker>
        </defs>

        {/* Inputs */}
        {[
          { y: 30, label: 'Microscopy', color: '#7AC6D9' },
          { y: 100, label: 'Spectroscopy', color: '#74CFC3' },
          { y: 170, label: 'Genomics', color: '#A8DAE7' },
          { y: 240, label: 'Clinical Data', color: '#A3B4C9' },
        ].map((row, i) => (
          <g key={i}>
            <rect x="40" y={row.y} width="100" height="32" rx="6" fill="#FFFFFF" stroke="#DCE7EC" />
            <text x="90" y={row.y + 20} textAnchor="middle" fontSize="11" fontWeight="500" fill="#16313F">
              {row.label}
            </text>
            <line x1="140" y1={row.y + 16} x2="180" y2={row.y + 16} stroke="#176B87" strokeWidth="1.4" strokeOpacity="0.5" markerEnd="url(#arrow2)" />
            <rect x="180" y={row.y} width="120" height="32" rx="6" fill="#EAF6FA" stroke="#D6EDF4" />
            <text x="240" y={row.y + 20} textAnchor="middle" fontSize="10" fontWeight="500" fill="#125570">
              {['Vision', 'Spectral', 'Genomic', 'Clinical'][i]} Encoder
            </text>
          </g>
        ))}

        {/* Converging lines into fusion */}
        {[46, 116, 186, 256].map((y, i) => (
          <path
            key={'cl' + i}
            d={`M 300 ${y} Q 320 ${y} 320 320`}
            stroke="#176B87"
            strokeWidth="1.2"
            strokeOpacity="0.45"
            fill="none"
            strokeDasharray="3 4"
          />
        ))}

        {/* Fusion block */}
        <rect x="190" y="300" width="180" height="50" rx="10" fill="url(#arcFill)" />
        <defs>
          <linearGradient id="arcFill" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#176B87" />
            <stop offset="100%" stopColor="#2A9D8F" />
          </linearGradient>
        </defs>

        <text x="280" y="322" textAnchor="middle" fontSize="11" fontWeight="600" fill="#FFFFFF">
          Cross-Attention
        </text>
        <text x="280" y="338" textAnchor="middle" fontSize="10" fill="#FFFFFF" opacity="0.9">
          Fusion Transformer
        </text>

        {/* Down arrow */}
        <line x1="280" y1="350" x2="280" y2="370" stroke="#176B87" strokeWidth="1.4" strokeOpacity="0.5" markerEnd="url(#arrow2)" />

        {/* Output */}
        <rect x="160" y="370" width="240" height="38" rx="8" fill="#FFFFFF" stroke="#176B87" strokeOpacity="0.4" />
        <text x="280" y="395" textAnchor="middle" fontSize="11" fontWeight="600" fill="#16313F">
          Biofilm Risk Prediction
        </text>

        <text x="280" y="430" textAnchor="middle" fontSize="10" fill="#607784">
          Multimodal Representation → Research Interpretation
        </text>
      </svg>
    </div>
  );
}

function MetricsSection() {
  return (
    <section className="py-20 sm:py-24 bg-white border-y border-border-subtle">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="grid lg:grid-cols-3 gap-10">
          <div className="lg:col-span-1">
            <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">
              Decision support
            </p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight text-ink text-balance">
              Model outputs that are transparent, auditable, and clearly a research artifact.
            </h2>
          </div>

          <div className="lg:col-span-2 grid sm:grid-cols-2 gap-5">
            {[
              {
                title: 'Modal-aware interpretations',
                body:
                  'Modality contribution views, attention overlays, and cross-attention matrices that show what the model focused on.',
                icon: Eye,
              },
              {
                title: 'Honest about uncertainty',
                body:
                  'Every output states whether it comes from a trained model or the demo pipeline, so simulated results are never mistaken for real ones.',
                icon: ShieldCheck,
              },
              {
                title: 'Research-grade transparency',
                body:
                  'Sample identifiers, modality availability, and pipeline steps are visible at every stage.',
                icon: FlaskConical,
              },
              {
                title: 'Privacy-aware by default',
                body:
                  'Avoids patient identifiers, validates uploads, and communicates that the system is for research use.',
                icon: ShieldCheck,
              },
            ].map((feat) => (
              <div key={feat.title} className="rounded-lg border border-border-subtle bg-surface-muted p-5">
                <div className="h-9 w-9 rounded-md bg-white text-primary flex items-center justify-center border border-border-subtle">
                  <feat.icon className="h-4 w-4" />
                </div>
                <h3 className="mt-3 text-sm font-semibold text-ink">{feat.title}</h3>
                <p className="mt-1.5 text-sm text-ink-secondary leading-relaxed">{feat.body}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function PrivacySection() {
  return (
    <section className="py-16 bg-surface-muted">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div className="rounded-xl border border-border bg-white p-6 sm:p-8 shadow-card">
          <div className="flex items-start gap-4">
            <div className="h-10 w-10 rounded-md bg-warning-50 text-warning flex items-center justify-center shrink-0">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <p className="text-[11px] font-semibold tracking-wider uppercase text-warning">
                Important
              </p>
              <h3 className="mt-1 text-lg font-semibold text-ink">
                Research prototype · not a diagnostic device
              </h3>
              <p className="mt-2 text-sm text-ink-secondary leading-relaxed max-w-3xl">
                BiofilmAI is a research prototype. Outputs are computational predictions and are
                not intended to diagnose, treat, or rule out disease. Results should not replace
                appropriate laboratory testing or professional clinical judgment.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function CTASection() {
  return (
    <section className="py-20 sm:py-24 bg-surface-muted">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
        <div className="rounded-2xl border border-border bg-white p-8 sm:p-12 shadow-soft text-center">
          <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">
            Get started
          </p>
          <h2 className="mt-3 text-3xl sm:text-4xl font-semibold tracking-tight text-ink text-balance">
            Run your first multimodal analysis.
          </h2>
          <p className="mt-4 text-base text-ink-secondary max-w-xl mx-auto">
            Upload microscopy, spectroscopy, and genomic evidence, enter structured clinical
            context, and review a research-oriented biofilm risk prediction with modality and
            attention interpretation.
          </p>
          <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
            <Link href="/analyze">
              <Button size="lg" iconRight={<ArrowRight className="h-4 w-4" />}>
                Start Analysis
              </Button>
            </Link>
            <Link href="/dashboard">
              <Button size="lg" variant="outline">
                View Dashboard
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
