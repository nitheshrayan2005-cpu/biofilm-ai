import Link from 'next/link';
import {
  Brain,
  Layers,
  Cpu,
  FlaskConical,
  ArrowRight,
  ShieldCheck,
  Microscope,
  Atom,
  Dna,
  ClipboardList,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardEyebrow } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';

export default function ResearchPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
      <div className="grid lg:grid-cols-12 gap-10">
        <div className="lg:col-span-8">
          <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">Research</p>
          <h1 className="mt-2 text-3xl sm:text-4xl font-semibold tracking-tight text-ink">
            Multimodal Transformer Architecture
          </h1>
          <p className="mt-4 text-base text-ink-secondary max-w-3xl leading-relaxed">
            BiofilmAI integrates microscopy, spectroscopy, genomic, and clinical data through
            a cross-attention transformer for rapid detection of biofilm-forming pathogens in
            chronic wound and implant infection.
          </p>

          <div className="mt-3">
            <Badge variant="warning" size="md" dot>
              Research prototype · No clinical claims
            </Badge>
          </div>

          <div className="mt-8 space-y-10">
            <Section title="Problem" icon={FlaskConical}>
              <p>
                Biofilms are microbial communities encased in a self-produced extracellular
                polymeric substance (EPS), which protects them from antibiotics and the immune
                system. Biofilm was found in 60% of chronic wound specimens but only 6% of acute
                wounds, and these communities were often polymicrobial (James et al., 2008).
              </p>
              <p>
                Standard culture takes 48–72 hours and cannot report biofilm presence, maturity,
                and drug resistance together. Each modality sees only part of the picture: images
                show structure, spectra show chemistry, genomes show species and resistance genes,
                and clinical data shows context. This project fuses all four.
              </p>
            </Section>

            <Section title="Proposed Approach" icon={Brain}>
              <p>
                Each modality has its own encoder that maps it into a shared latent space. A
                cross-attention transformer then lets every modality attend to the others before
                the fused representation reaches the prediction head.
              </p>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-4">
                <EncoderCard icon={Microscope} name="Vision Encoder" sub="ViT patches" />
                <EncoderCard icon={Atom} name="Spectral Encoder" sub="Transformer" />
                <EncoderCard icon={Dna} name="Genomic Encoder" sub="k-mer Transformer" />
                <EncoderCard icon={ClipboardList} name="Clinical Encoder" sub="MLP" />
              </div>
              <div className="mt-4 rounded-lg border border-border bg-white p-5">
                <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-secondary mb-3">
                  Fusion
                </p>
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="rounded-md bg-primary-50 text-primary-700 px-2.5 py-1 font-medium border border-primary-100">
                    Encoded modalities
                  </span>
                  <Arrow />
                  <span className="rounded-md bg-primary text-white px-2.5 py-1 font-medium">
                    Cross-Attention Transformer
                  </span>
                  <Arrow />
                  <span className="rounded-md bg-primary-50 text-primary-700 px-2.5 py-1 font-medium border border-primary-100">
                    Multimodal representation
                  </span>
                  <Arrow />
                  <span className="rounded-md bg-surface-muted text-ink px-2.5 py-1 font-medium border border-border">
                    Prediction head
                  </span>
                </div>
              </div>
            </Section>

            <Section title="Data Flow" icon={Layers}>
              <p>
                Each modality enters the pipeline through a standardized preprocessing step and is
                reduced to a sequence of tokens consumed by its respective encoder.
              </p>
              <div className="mt-4 rounded-lg border border-border bg-white p-5">
                <DataFlowDiagram />
              </div>
            </Section>

            <Section title="Evaluation" icon={ShieldCheck}>
              <p>
                The four-modality model will be reported on a held-out test set once a dataset with
                all four modalities for the same samples is available. Results for the models
                already trained on real data are in the Results panel.
              </p>
            </Section>
          </div>
        </div>

        <div className="lg:col-span-4 space-y-5">
          <Card>
            <CardEyebrow>Results</CardEyebrow>
            <CardTitle className="mt-1">Model comparison</CardTitle>
            <CardDescription className="mt-1">
              Genomic classifier: 103 <em>S. epidermidis</em> isolates, pathogenic vs commensal.
            </CardDescription>

            <div className="-mx-5 mt-4 overflow-x-auto">
              <table className="w-full text-sm min-w-[480px]">
                <thead>
                  <tr className="border-t border-b border-border-subtle bg-surface-muted/40">
                    <TH>Model</TH>
                    <TH>Mod.</TH>
                    <TH>F1</TH>
                    <TH>ROC</TH>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { name: 'Genomic LR (5-fold CV)', mod: 'G', f1: '0.76', roc: '0.80' },
                    { name: 'Genomic LR (test set)', mod: 'G', f1: '0.76', roc: '0.75' },
                  ].map((row) => (
                    <tr key={row.name} className="border-b border-border-subtle/60">
                      <td className="px-5 py-2.5 text-sm text-ink">{row.name}</td>
                      <td className="px-5 py-2.5 text-[12px] font-mono text-ink-secondary">{row.mod}</td>
                      <td className="px-5 py-2.5 text-[12px] text-ink-secondary">{row.f1}</td>
                      <td className="px-5 py-2.5 text-[12px] text-ink-secondary">{row.roc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          <Card>
            <CardEyebrow>Next step</CardEyebrow>
            <CardTitle className="mt-1">Try the workflow</CardTitle>
            <CardDescription className="mt-1">
              Run a demo analysis to see how modalities travel through the model.
            </CardDescription>
            <Link href="/analyze" className="block mt-4">
              <Button fullWidth iconRight={<ArrowRight className="h-4 w-4" />}>
                Start Analysis
              </Button>
            </Link>
          </Card>
        </div>
      </div>
    </div>
  );
}

function Section({ title, icon: Icon, children }: { title: string; icon: any; children: React.ReactNode }) {
  return (
    <section>
      <div className="flex items-center gap-3 mb-4">
        <div className="h-9 w-9 rounded-md bg-primary-50 text-primary flex items-center justify-center">
          <Icon className="h-4 w-4" />
        </div>
        <h2 className="text-xl font-semibold text-ink">{title}</h2>
      </div>
      <div className="prose prose-sm max-w-none text-ink-secondary leading-relaxed space-y-3 [&_p]:text-ink-secondary">
        {children}
      </div>
    </section>
  );
}

function EncoderCard({ icon: Icon, name, sub }: { icon: any; name: string; sub: string }) {
  return (
    <div className="rounded-md border border-border bg-white px-3 py-3">
      <div className="h-7 w-7 rounded-md bg-primary-50 text-primary flex items-center justify-center mb-2">
        <Icon className="h-3.5 w-3.5" />
      </div>
      <p className="text-[13px] font-semibold text-ink">{name}</p>
      <p className="text-[11px] text-ink-secondary">{sub}</p>
    </div>
  );
}

function Arrow() {
  return <ArrowRight className="h-3.5 w-3.5 text-ink-secondary" />;
}

function TH({ children }: { children?: React.ReactNode }) {
  return (
    <th className="text-left px-5 py-2 text-[11px] font-semibold uppercase tracking-wider text-ink-secondary">
      {children}
    </th>
  );
}

function DataFlowDiagram() {
  const stages = [
    { title: 'Raw inputs', sub: 'Image · spectra · sequence · fields', icon: Layers },
    { title: 'Preprocessing', sub: 'Per-modality pipeline', icon: Cpu },
    { title: 'Modality encoders', sub: '4 × encoders', icon: Brain },
    { title: 'Cross-attention fusion', sub: 'Joint representation', icon: Layers },
    { title: 'Prediction', sub: 'Biofilm probability', icon: ShieldCheck },
  ];
  return (
    <div className="grid grid-flow-col auto-cols-fr gap-2">
      {stages.map((s, i) => (
        <div key={s.title} className="relative">
          <div className="h-full rounded-md border border-border bg-surface-muted/40 p-3 relative">
            <div className="flex items-center gap-2 mb-2">
              <s.icon className="h-3.5 w-3.5 text-primary" />
              <p className="text-[11px] font-semibold uppercase tracking-wider text-ink-secondary">
                Step 0{i + 1}
              </p>
            </div>
            <p className="text-sm font-medium text-ink">{s.title}</p>
            <p className="text-[11px] text-ink-secondary mt-0.5">{s.sub}</p>
          </div>
          {i < stages.length - 1 && (
            <ArrowRight className="absolute top-1/2 -right-3 h-3.5 w-3.5 text-ink-secondary -translate-y-1/2" />
          )}
        </div>
      ))}
    </div>
  );
}
