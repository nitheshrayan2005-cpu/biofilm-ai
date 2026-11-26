// Display labels for the coded values the Analyze form stores, so the
// Results page and PDF report show "Orthopedic implant", not "orthopedic-implant".

const LABELS: Record<string, Record<string, string>> = {
  infectionContext: {
    'chronic-wound': 'Chronic wound',
    'orthopedic-implant': 'Orthopedic implant',
    catheter: 'Catheter-associated',
    'post-surgical': 'Post-surgical',
  },
  previousTreatment: {
    none: 'None',
    antibiotics: 'Antibiotics',
    'surgical-debridement': 'Surgical debridement',
    combination: 'Combination',
  },
  previousCulture: {
    negative: 'Negative',
    'positive-mixed': 'Positive (mixed flora)',
    'positive-pure': 'Positive (pure culture)',
    unknown: 'Unknown',
  },
};

/** Human-readable label for a stored form value; unknown codes pass through. */
export function clinicalLabel(field: keyof typeof LABELS, value: string | undefined | null): string {
  if (!value) return '—';
  return LABELS[field]?.[value] ?? value;
}

/** Plain-language meaning of each risk category (thresholds match the backend). */
export const RISK_MEANING: Record<string, string> = {
  low: 'Low (below 40%): the combined evidence does not suggest a biofilm-associated infection.',
  intermediate: 'Intermediate (40-69%): some features are consistent with a biofilm-associated infection.',
  high: 'High (70% or above): the combined evidence is consistent with a biofilm-associated infection.',
};
