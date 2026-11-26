'use client';

import { Microscope, Atom, Dna, ClipboardList } from 'lucide-react';

/**
 * Four-modality scientific visualization for the landing hero.
 * Renders the data flow: microscopy, spectroscopy, genomics, clinical -> fusion -> prediction.
 * Pure SVG + CSS animations to remain lightweight.
 */
export function HeroVisualization() {
  return (
    <div className="relative w-full aspect-[5/4] max-w-[640px] mx-auto">
      <div className="absolute inset-0 -m-12 blur-3xl opacity-40 pointer-events-none">
        <div className="absolute top-8 left-8 h-40 w-40 rounded-full bg-primary-100" />
        <div className="absolute bottom-8 right-8 h-40 w-40 rounded-full bg-secondary/10" />
      </div>

      <svg
        viewBox="0 0 600 480"
        className="w-full h-full relative"
        aria-label="Multimodal AI architecture diagram for biofilm analysis"
        role="img"
      >
        <defs>
          <linearGradient id="fusionFill" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#176B87" />
            <stop offset="100%" stopColor="#2A9D8F" />
          </linearGradient>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="10"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#176B87" opacity="0.7" />
          </marker>
          {/* Paths for flowing particles */}
          {[
            { id: 'p1', x1: 100, y1: 148, x2: 310, y2: 340 },
            { id: 'p2', x1: 260, y1: 148, x2: 310, y2: 340 },
            { id: 'p3', x1: 420, y1: 148, x2: 310, y2: 340 },
            { id: 'p4', x1: 100, y1: 268, x2: 310, y2: 340 },
          ].map((p) => {
            const cx = (p.x1 + p.x2) / 2;
            const cy = p.y1 + (p.y2 - p.y1) * 0.3;
            return (
              <path
                key={p.id}
                id={p.id}
                d={`M ${p.x1} ${p.y1} Q ${cx} ${cy} ${p.x2} ${p.y2}`}
                fill="none"
              />
            );
          })}
        </defs>

        {/* Background dotted grid */}
        <g opacity="0.35">
          {Array.from({ length: 12 }).map((_, i) => (
            <line key={'v' + i} x1={i * 50 + 10} y1="20" x2={i * 50 + 10} y2="460" stroke="#DCE7EC" strokeWidth="0.5" />
          ))}
          {Array.from({ length: 9 }).map((_, i) => (
            <line key={'h' + i} x1="20" y1={i * 50 + 20} x2="580" y2={i * 50 + 20} stroke="#DCE7EC" strokeWidth="0.5" />
          ))}
        </g>

        {/* Curved connectors */}
        {[
          { x1: 100, y1: 148, x2: 310, y2: 340 },
          { x1: 260, y1: 148, x2: 310, y2: 340 },
          { x1: 420, y1: 148, x2: 310, y2: 340 },
          { x1: 100, y1: 268, x2: 310, y2: 340 },
        ].map((p, i) => {
          const cx = (p.x1 + p.x2) / 2;
          const cy = p.y1 + (p.y2 - p.y1) * 0.3;
          return (
            <g key={'conn' + i}>
              <path
                d={`M ${p.x1} ${p.y1} Q ${cx} ${cy} ${p.x2} ${p.y2}`}
                stroke="#176B87"
                strokeOpacity="0.35"
                strokeWidth="1.5"
                fill="none"
                strokeDasharray="3 4"
                className="particle-line"
              />
              <circle r="3" fill="#176B87" className="dot-flow" style={{ animationDelay: `${i * 0.5}s` }}>
                <animateMotion dur="2.6s" repeatCount="indefinite" begin={`${i * 0.5}s`}>
                  <mpath href={`#p${i + 1}`} />
                </animateMotion>
              </circle>
            </g>
          );
        })}

        {/* Modality nodes */}
        {[
          { x: 50, y: 50, label: 'Microscopy', icon: 'microscope' },
          { x: 210, y: 50, label: 'Spectroscopy', icon: 'atom' },
          { x: 370, y: 50, label: 'Genomics', icon: 'dna' },
        ].map((m, i) => (
          <foreignObject key={'m' + i} x={m.x} y={m.y} width="160" height="44">
            <div className="w-full h-full rounded-lg bg-white border border-border flex items-center gap-2 px-2.5 shadow-card">
              <div className="h-7 w-7 rounded-md bg-primary-50 text-primary flex items-center justify-center shrink-0">
                {m.icon === 'microscope' && <Microscope className="h-3.5 w-3.5" />}
                {m.icon === 'atom' && <Atom className="h-3.5 w-3.5" />}
                {m.icon === 'dna' && <Dna className="h-3.5 w-3.5" />}
              </div>
              <span className="text-[12px] font-medium text-ink leading-none">{m.label}</span>
            </div>
          </foreignObject>
        ))}

        {/* Clinical row */}
        <foreignObject x={50} y={170} width="160" height="44">
          <div className="w-full h-full rounded-lg bg-white border border-border flex items-center gap-2 px-2.5 shadow-card">
            <div className="h-7 w-7 rounded-md bg-primary-50 text-primary flex items-center justify-center shrink-0">
              <ClipboardList className="h-3.5 w-3.5" />
            </div>
            <span className="text-[12px] font-medium text-ink leading-none">Clinical Data</span>
          </div>
        </foreignObject>

        {/* Encoder chips */}
        {[
          { x: 58, y: 110, label: 'Vision Encoder' },
          { x: 218, y: 110, label: 'Spectral Enc.' },
          { x: 378, y: 110, label: 'Genomic Enc.' },
          { x: 58, y: 230, label: 'Clinical Enc.' },
        ].map((e, i) => (
          <g key={'enc' + i}>
            <rect x={e.x} y={e.y} width="92" height="22" rx="6" fill="#EAF6FA" stroke="#D6EDF4" />
            <text x={e.x + 46} y={e.y + 15} textAnchor="middle" fontSize="10" fontWeight="500" fill="#125570">
              {e.label}
            </text>
          </g>
        ))}

        {/* Fusion engine */}
        <foreignObject x="180" y="320" width="240" height="80">
          <div className="w-full h-full rounded-xl bg-gradient-to-br from-primary to-secondary border border-primary/40 px-4 text-center flex flex-col items-center justify-center shadow-lifted animate-fade-in">
            <div className="text-[10px] tracking-widest uppercase text-white/80">Multimodal Transformer</div>
            <div className="text-sm font-semibold mt-0.5 text-white">Cross-Attention Fusion</div>
          </div>
        </foreignObject>

        {/* Output */}
        <foreignObject x="180" y="410" width="240" height="52">
          <div className="w-full h-full rounded-lg bg-white border border-border flex items-center justify-center px-4 text-center shadow-card animate-fade-in">
            <div>
              <div className="text-[10px] tracking-widest uppercase text-ink-secondary">Output</div>
              <div className="text-sm font-semibold text-ink">Biofilm Risk Prediction</div>
            </div>
          </div>
        </foreignObject>

        <line x1="300" y1="400" x2="300" y2="410" stroke="#176B87" strokeWidth="1.5" opacity="0.5" />
      </svg>
    </div>
  );
}
