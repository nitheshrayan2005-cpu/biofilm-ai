import { FlaskConical } from 'lucide-react';

export function DemoBadge({ small = false }: { small?: boolean }) {
  return (
    <div className={`inline-flex items-center gap-2 rounded-md border border-warning-100 bg-warning-50 px-3 py-1.5 text-warning-700 ${
      small ? 'text-[11px]' : 'text-[12px]'
    }`}>
      <FlaskConical className={small ? 'h-3 w-3' : 'h-3.5 w-3.5'} />
      <span className="font-medium">Demo mode</span>
      <span className="text-warning-700/80 hidden sm:inline">
        Predictions are simulated. No clinical prediction is generated.
      </span>
    </div>
  );
}
