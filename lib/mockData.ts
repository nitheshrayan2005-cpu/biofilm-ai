// Demo / mock data used until the real multimodal Transformer backend is
// wired in. Every value here is clearly indicated to the user as simulated.

import { AnalysisSummary, AnalysisResponse, ModalityName } from './types';
import { classifyRisk } from './api';

const sampleTypes = ['Wound swab', 'Implant sonicate', 'Tissue biopsy', 'Sputum', 'Blood culture', 'Urine sample'];
const infectionContexts = ['Chronic wound', 'Orthopedic implant', 'Catheter-associated', 'Post-surgical', 'Burn wound', 'Periodontal'];
const sampleSites = ['Abdomen', 'Knee (prosthetic)', 'Lower leg', 'Forearm', 'Hip', 'Mandible'];

function pseudoRandom(seed: number): () => number {
  return () => {
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
  };
}

const rng = pseudoRandom(42);

function makeSummary(idx: number): AnalysisSummary {
  const sampleType = sampleTypes[idx % sampleTypes.length];
  const isHigh = rng() > 0.55;
  const isInter = !isHigh && rng() > 0.5;
  const prob = isHigh ? 0.72 + rng() * 0.25 : isInter ? 0.4 + rng() * 0.28 : 0.08 + rng() * 0.3;
  const days = Math.floor(rng() * 22) + 1;
  const hasAll = rng() > 0.2;

  const modalities: ModalityName[] = ['microscopy', 'spectroscopy', 'clinical'];
  if (rng() > 0.3) modalities.push('genomics');

  const d = new Date();
  d.setDate(d.getDate() - idx * 2 - Math.floor(rng() * 2));

  return {
    analysisId: `BA-${(2400 + idx * 7).toString().padStart(5, '0')}`,
    sampleId: `S-${(1840 + idx * 3).toString().padStart(5, '0')}`,
    sampleType,
    createdAt: d.toISOString(),
    modalities,
    prediction: {
      biofilmProbability: Math.round(prob * 1000) / 1000,
      riskCategory: classifyRisk(prob),
    },
    status: 'completed',
  };
}

export const MOCK_HISTORY: AnalysisSummary[] = Array.from({ length: 18 }, (_, i) => makeSummary(i));

// Generate a synthetic multimodal analysis response.
export function generateMockAnalysis(_req: unknown): AnalysisResponse {
  const rng2 = pseudoRandom(Math.floor(Math.random() * 100000));
  const probability = rng2() * 0.85 + 0.08;
  const analysisId = `BA-${Math.floor(2500 + rng2() * 4000)}`;
  const now = new Date().toISOString();
  const completed = new Date(Date.now() + 6000).toISOString();

  return {
    analysisId,
    status: 'completed',
    createdAt: now,
    completedAt: completed,
    prediction: {
      biofilmProbability: Math.round(probability * 1000) / 1000,
      riskCategory: classifyRisk(probability),
    },
    modalities: {
      microscopy: { modality: 'microscopy', available: true, status: 'available' },
      spectroscopy: { modality: 'spectroscopy', available: true, status: 'available' },
      genomics: { modality: 'genomics', available: true, status: 'available' },
      clinical: { modality: 'clinical', available: true, status: 'available' },
    },
    interpretation: {
      microscopyAttention: {
        originalAvailable: true,
        overlayAvailable: true,
        heatmapAvailable: true,
      },
      crossAttention: generateMockAttentionMap(),
    },
    demoMode: true,
  };
}

// 4x4 cross-attention matrix with science-informed style biases.
export function generateMockAttentionMap() {
  const rows: ModalityName[] = ['microscopy', 'spectroscopy', 'genomics', 'clinical'];
  const cols: ModalityName[] = rows.slice();
  const rng3 = pseudoRandom(99);
  const base = [
    [0.38, 0.22, 0.18, 0.22],
    [0.24, 0.34, 0.20, 0.22],
    [0.20, 0.22, 0.32, 0.26],
    [0.22, 0.24, 0.28, 0.26],
  ];
  const values = base.map((r) => r.map((v) => Math.max(0.05, Math.min(0.95, v + (rng3() - 0.5) * 0.06))));
  return { rows, cols, values };
}

// Generate a synthetic spectral profile for previewing spectroscopy files.
export function generateSampleSpectra(): { wavelength: number; intensity: number }[] {
  const points: { wavelength: number; intensity: number }[] = [];
  for (let i = 0; i < 80; i++) {
    const w = 400 + i * 10;
    const base =
      Math.sin(i * 0.18) * 0.35 +
      Math.cos(i * 0.05) * 0.18 +
      Math.exp(-Math.pow((i - 35) / 8, 2)) * 0.55 +
      Math.exp(-Math.pow((i - 62) / 12, 2)) * 0.32 +
      (Math.random() - 0.5) * 0.05;
    points.push({ wavelength: w, intensity: Math.max(0.02, Math.min(1, base + 0.2)) });
  }
  return points;
}

// Time-series for activity chart
export function generateActivitySeries() {
  const series: { date: string; analyses: number; high: number }[] = [];
  for (let i = 13; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    series.push({
      date: d.toISOString().slice(5, 10),
      analyses: Math.floor(Math.random() * 9) + 3,
      high: Math.floor(Math.random() * 4),
    });
  }
  return series;
}

export { sampleTypes, infectionContexts, sampleSites };
