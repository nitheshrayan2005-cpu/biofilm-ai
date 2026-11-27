import { FlaskConical } from 'lucide-react';

// Shown on analysis pages: the score is rule-based (computed from measured
// evidence), not a trained-AI prediction and not a diagnosis.
export function DemoBadge({ small = false }: { small?: boolean }) {
  return (
    <div className={`inline-flex items-center gap-2 rounded-md border border-warning-100 bg-warning-50 px-3 py-1.5 text-warning-700 ${
      small ? 'text-[11px]' : 'text-[12px]'
    }`}>
      <FlaskConical className={small ? 'h-3 w-3' : 'h-3.5 w-3.5'} />
      <span className="font-medium">Research prototype</span>
      <span className="text-warning-700/80 hidden sm:inline">
        Not a clinical diagnosis.
      </span>
    </div>
  );
}
