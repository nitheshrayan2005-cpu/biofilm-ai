import Link from 'next/link';
import {
  ShieldCheck,
  Brain,
  ArrowRight,
  Microscope,
  Atom,
  Dna,
  ClipboardList,
  Upload,
  FileText,
} from 'lucide-react';
import { Card, CardTitle, CardEyebrow } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LogoMark } from '@/components/layout/Logo';

const steps = [
  { icon: ClipboardList, title: 'Register the sample', text: 'Coded sample and study IDs, sample type and infection context. No patient names.' },
  { icon: Upload, title: 'Add the evidence', text: 'Microscopy image, Raman spectrum, genome and clinical details. Any of them may be missing.' },
  { icon: Brain, title: 'Combine the evidence', text: 'Each evidence type is measured separately, then combined into one score with a clear verdict for each.' },
  { icon: FileText, title: 'Review and report', text: 'A risk estimate with its evidence summary, kept in history and exportable as a PDF report.' },
];

const encoders = [
  { icon: Microscope, name: 'Microscopy', model: 'Vision Transformer' },
  { icon: Atom, name: 'Raman spectroscopy', model: '1D Transformer' },
  { icon: Dna, name: 'Genomics', model: 'Sequence Transformer' },
  { icon: ClipboardList, name: 'Clinical data', model: 'Multilayer perceptron' },
];

export default function AboutPage() {
  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-b from-primary-50/70 to-transparent border-b border-border-subtle">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16 sm:py-20">
          <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">About BiofilmAI</p>
          <h1 className="mt-3 text-3xl sm:text-5xl font-semibold tracking-tight text-ink max-w-4xl leading-tight">
            One view of the evidence behind biofilm infections.
          </h1>
          <p className="mt-5 text-lg text-ink-secondary max-w-3xl leading-relaxed">
            BiofilmAI brings microscopy, Raman spectroscopy, genomics and clinical data for a sample
            together, measures each piece of evidence, and combines them into a single, explainable
            risk estimate for chronic wound and implant infections.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/analyze">
              <Button size="lg" iconRight={<ArrowRight className="h-4 w-4" />}>Start an analysis</Button>
            </Link>
            <a href="#how-it-works">
              <Button size="lg" variant="outline">How it works</Button>
            </a>
          </div>
        </div>
      </section>

      {/* Mission */}
      <section className="py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 grid lg:grid-cols-2 gap-10 lg:gap-16">
          <div>
            <SectionLabel>Our mission</SectionLabel>
            <h2 className="mt-2 text-2xl sm:text-3xl font-semibold text-ink">
              Faster, better-informed decisions about biofilm infection
            </h2>
          </div>
          <div className="space-y-4 text-base text-ink-secondary leading-relaxed">
            <p>
              Biofilm-forming bacteria such as <em>P. aeruginosa</em>, <em>S. aureus</em> and{' '}
              <em>S. epidermidis</em> shelter inside a self-produced matrix that protects them from
              antibiotics and the immune system. Biofilm has been found in 60% of chronic wound
              specimens but only 6% of acute wounds (James et al., 2008).
            </p>
            <p>
              Standard culture takes 48–72 hours and often misses biofilm. Each laboratory test shows
              only part of the picture, and the reports are read side by side by hand. BiofilmAI is
              built to combine that evidence in one place, consistently and transparently.
            </p>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="py-16 bg-surface-muted/40 border-y border-border-subtle scroll-mt-20">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <SectionLabel>How it works</SectionLabel>
          <h2 className="mt-2 text-2xl sm:text-3xl font-semibold text-ink">From sample to report in four steps</h2>
          <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {steps.map((s, i) => (
              <Card key={s.title} padding="lg" className="h-full">
                <div className="flex items-center justify-between">
                  <div className="h-10 w-10 rounded-md bg-primary-50 text-primary flex items-center justify-center">
                    <s.icon className="h-5 w-5" />
                  </div>
                  <span className="text-xs font-mono text-ink-secondary">0{i + 1}</span>
                </div>
                <h3 className="mt-4 text-base font-semibold text-ink">{s.title}</h3>
                <p className="mt-2 text-sm text-ink-secondary leading-relaxed">{s.text}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Technology */}
      <section className="py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <SectionLabel>Technology</SectionLabel>
          <h2 className="mt-2 text-2xl sm:text-3xl font-semibold text-ink">Built for multimodal AI</h2>
          <p className="mt-3 text-base text-ink-secondary max-w-3xl leading-relaxed">
            Today, BiofilmAI analyses microscopy images, Raman spectra and genomes directly, and uses a
            machine-learning model trained on 103 real genomes. Its multimodal Transformer, with a
            dedicated encoder for every evidence type and cross-attention between them, is built and
            ready to be trained as paired clinical data becomes available.
          </p>
          <div className="mt-8 grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {encoders.map((e) => (
              <div key={e.name} className="rounded-lg border border-border bg-white p-5">
                <e.icon className="h-5 w-5 text-primary" />
                <p className="mt-3 text-sm font-semibold text-ink">{e.name}</p>
                <p className="text-sm text-primary-700">{e.model}</p>
              </div>
            ))}
          </div>
          <div className="mt-5 rounded-lg border border-border bg-white p-5 flex flex-wrap items-center gap-2 text-sm">
            <Pill>Four encoders</Pill>
            <ArrowRight className="h-4 w-4 text-ink-secondary" />
            <Pill strong>Cross-attention fusion</Pill>
            <ArrowRight className="h-4 w-4 text-ink-secondary" />
            <Pill>Prediction head</Pill>
            <ArrowRight className="h-4 w-4 text-ink-secondary" />
            <Pill>Risk estimate and explanation</Pill>
          </div>
        </div>
      </section>

      {/* Responsible use + CTA */}
      <section className="pb-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 grid lg:grid-cols-3 gap-5">
          <div className="lg:col-span-2 rounded-lg border border-warning-100 bg-warning-50/60 p-6 flex gap-4">
            <ShieldCheck className="h-6 w-6 text-warning shrink-0" />
            <div>
              <p className="text-sm font-semibold text-ink">Responsible use</p>
              <p className="mt-1 text-sm text-ink leading-relaxed">
                BiofilmAI is a research prototype and is not a medical device. Its outputs are
                computational estimates that support, and never replace, laboratory confirmation and
                professional clinical judgement. It must not be used to diagnose or treat patients.
              </p>
            </div>
          </div>
          <Card padding="lg" className="flex flex-col justify-between">
            <div className="flex items-center gap-3">
              <LogoMark size="lg" />
              <div>
                <CardTitle>BiofilmAI</CardTitle>
                <CardEyebrow className="mt-0.5">Version 0.1.0 · Research preview</CardEyebrow>
              </div>
            </div>
            <Link href="/analyze" className="block mt-5">
              <Button fullWidth iconRight={<ArrowRight className="h-4 w-4" />}>Start an analysis</Button>
            </Link>
          </Card>
        </div>
      </section>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">{children}</p>;
}

function Pill({ children, strong }: { children: React.ReactNode; strong?: boolean }) {
  return (
    <span
      className={
        strong
          ? 'rounded-md bg-primary text-white px-3 py-1 font-medium'
          : 'rounded-md bg-primary-50 text-primary-700 px-3 py-1 font-medium border border-primary-100'
      }
    >
      {children}
    </span>
  );
}
