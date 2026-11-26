import Link from 'next/link';
import {
  ShieldCheck,
  FlaskConical,
  Brain,
  ArrowRight,
  CheckCircle2,
  CircleDashed,
  Database,
  Sparkles,
  Users,
  Globe,
} from 'lucide-react';
import { Card, CardTitle, CardEyebrow } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Logo, LogoMark } from '@/components/layout/Logo';

const milestones = [
  { label: 'Dataset preparation', complete: true, icon: Database },
  { label: 'Modality encoders', complete: true, icon: Brain },
  { label: 'Multimodal fusion', complete: true, icon: Sparkles },
  { label: 'Backend integration', complete: true, icon: FlaskConical },
  { label: 'Multimodal training', complete: false, icon: ShieldCheck },
  { label: 'Clinical validation', complete: false, icon: Globe },
];

const team = ['Nithesh Rayan R', 'Nitin Kumar M', 'Hithysh R Gowda'];

export default function AboutPage() {
  return (
    <div>
      <section className="bg-gradient-to-b from-primary-50/60 to-transparent border-b border-border-subtle">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16">
          <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">About</p>
          <h1 className="mt-2 text-3xl sm:text-4xl font-semibold tracking-tight text-ink">
            About BiofilmAI
          </h1>
          <p className="mt-4 text-base text-ink-secondary max-w-3xl leading-relaxed">
            A Multi-Modal Transformer Framework Integrating Microscopy, Spectroscopy, Genomics, and
            Clinical Data with Cross-Attention Fusion for Rapid Detection of Biofilm-Forming
            Pathogens in Chronic Wound and Implant Infection.
          </p>
        </div>
      </section>

      <section className="py-12 sm:py-16">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 grid lg:grid-cols-3 gap-10">
          <div className="lg:col-span-2 space-y-10">
            <div>
              <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">
                Problem statement
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-ink">Why multimodal?</h2>
              <p className="mt-3 text-base text-ink-secondary leading-relaxed">
                Biofilm-forming pathogens such as <em>P. aeruginosa</em>, <em>S. aureus</em>, and{' '}
                <em>S. epidermidis</em> live inside a self-produced extracellular polymeric
                substance (EPS) that makes them resistant to antibiotics and hard to detect.
                Culture takes 48–72 hours and often misses biofilm presence, maturity, and drug
                resistance. No existing system combines microscopy, spectroscopy, genomics, and
                clinical data in one deep learning framework to answer these questions together.
              </p>
            </div>

            <div>
              <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">
                Model architecture
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-ink">Cross-attention fusion</h2>
              <p className="mt-3 text-base text-ink-secondary leading-relaxed">
                Each modality has its own transformer encoder (image patches, spectral segments,
                sequence k-mers, and an MLP for clinical fields). A cross-attention transformer
                learns relationships across modalities and produces a unified representation that
                the prediction head maps to a biofilm-associated probability.
              </p>
            </div>

            <div>
              <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">
                Clinical motivation
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-ink">Why chronic wounds and implants?</h2>
              <p className="mt-3 text-base text-ink-secondary leading-relaxed">
                James et al. (2008) found biofilm in 60% of chronic wound specimens but only 6% of
                acute wounds, and showed that molecular methods detect bacteria, including
                anaerobes, that standard culture misses. Combining evidence types is how this
                project aims to close that gap.
              </p>
            </div>

            <div>
              <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">
                Current status
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-ink">Where the project stands</h2>
              <p className="mt-3 text-base text-ink-secondary leading-relaxed">
                The web application, FastAPI backend, and the multimodal model code (encoders and
                cross-attention fusion) are complete. Two research models are trained on real data:
                a genomic classifier and a biofilm thickness regressor. The full four-modality
                model is not trained yet because no public dataset has all four modalities for the
                same samples, so the analysis page returns clearly labeled demo values.
              </p>

              <div className="mt-5 rounded-lg border border-border bg-white p-5">
                <ol className="grid sm:grid-cols-3 lg:grid-cols-6 gap-3">
                  {milestones.map((m, i) => (
                    <li key={m.label} className="rounded-md border border-border-subtle bg-surface-muted/40 p-3">
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-[10px] font-mono text-ink-secondary">0{i + 1}</span>
                        {m.complete ? (
                          <CheckCircle2 className="h-4 w-4 text-success" />
                        ) : (
                          <CircleDashed className="h-4 w-4 text-ink-secondary" />
                        )}
                      </div>
                      <div className="h-7 w-7 rounded-md bg-primary-50 text-primary flex items-center justify-center mb-2">
                        <m.icon className="h-3.5 w-3.5" />
                      </div>
                      <p className="text-[12px] font-medium text-ink leading-tight">{m.label}</p>
                    </li>
                  ))}
                </ol>
              </div>
            </div>

            <div>
              <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">
                Research disclaimer
              </p>
              <div className="mt-3 rounded-lg border border-warning-100 bg-warning-50/60 p-5">
                <div className="flex gap-3">
                  <ShieldCheck className="h-5 w-5 text-warning shrink-0 mt-0.5" />
                  <p className="text-sm text-ink leading-relaxed">
                    BiofilmAI is a research prototype. Outputs are computational predictions and
                    are not intended to diagnose, treat, or rule out disease. Results should not
                    replace appropriate laboratory testing or professional clinical judgment.
                  </p>
                </div>
              </div>
            </div>

          </div>

          <div className="space-y-5">
            <Card padding="lg">
              <div className="flex items-center gap-3">
                <LogoMark size="lg" />
                <div>
                  <CardTitle>BiofilmAI</CardTitle>
                  <p className="text-xs text-ink-secondary">Biofilm Pathogen Detection</p>
                </div>
              </div>
              <dl className="mt-5 space-y-3 text-sm">
                <Row label="Version" value="0.1.0 · Research preview" />
                <Row label="Architecture" value="Cross-attention Transformer" />
                <Row label="Modalities" value="Microscopy · Spectroscopy · Genomics · Clinical" />
              </dl>
              <Link href="/research" className="block mt-5">
                <Button fullWidth variant="outline" iconRight={<ArrowRight className="h-4 w-4" />}>
                  Read the methodology
                </Button>
              </Link>
            </Card>

            <Card padding="lg">
              <CardEyebrow>Team</CardEyebrow>
              <CardTitle className="mt-1">Project team</CardTitle>
              <p className="mt-2 text-sm text-ink-secondary leading-relaxed">
                Guide: Mr. Vishal K, Assistant Professor, Dept. of ISE. Head of Department:
                Dr. Rashmi R Deshpande.
              </p>
              <div className="mt-4 grid grid-cols-3 gap-3 text-center text-xs">
                {team.map((name) => (
                  <div key={name} className="rounded-md bg-surface-muted p-3">
                    <Users className="h-4 w-4 text-primary mx-auto" />
                    <p className="font-medium mt-1">{name}</p>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>
      </section>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3 py-1.5 border-b border-border-subtle last:border-0">
      <dt className="text-ink-secondary text-[13px]">{label}</dt>
      <dd className="text-ink text-[13px] font-medium text-right">{value}</dd>
    </div>
  );
}
