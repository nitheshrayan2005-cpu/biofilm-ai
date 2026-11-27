// Core domain types for the BiofilmAI research platform

export type RiskCategory = 'low' | 'intermediate' | 'high';

export type AnalysisStatus = 'draft' | 'processing' | 'completed' | 'failed';

export type ModalityName = 'microscopy' | 'spectroscopy' | 'genomics' | 'clinical';

export interface SampleInfo {
  sampleId: string;
  studyId: string;
  sampleType: string;
  collectionDate: string;
  infectionContext: string;
  woundOrImplant: string;
  notes: string;
}

export interface ClinicalData {
  infectionContext: string;
  chronicityDays: number;
  implantPresent: boolean;
  sampleSite: string;
  previousTreatment: string;
  previousCulture: string;
  additionalNotes: string;
}

export interface ModalityFileMeta {
  name: string;
  size: number;
  type: string;
  uploadedAt: string;
}

export interface MicroscopyMeta extends ModalityFileMeta {
  width?: number;
  height?: number;
}

export interface SpectroscopyMeta extends ModalityFileMeta {
  points?: number;
  wavelengthRange?: [number, number];
}

export interface GenomicsMeta extends ModalityFileMeta {
  format: 'fasta' | 'csv' | 'txt' | 'unknown';
  organism?: string;
  featureCount?: number;
  sequenceLength?: number;
}

export interface ModalityRepresentation {
  modality: ModalityName;
  available: boolean;
  status: 'available' | 'unavailable';
  // When the backend provides actual modality contribution metrics:
  contributionScore?: number;
  embedding?: number[];
  attentionMapUrl?: string;
}

export interface CrossAttentionMap {
  rows: ModalityName[];
  cols: ModalityName[];
  values: number[][];
}

export interface PredictionResult {
  biofilmProbability: number;
  riskCategory: RiskCategory;
}

// ── Measured evidence (backend/evidence.py) ──────────────────────────────

export interface MicroscopyEvidence {
  stain: string;
  coverage_pct: number;
  cluster_count: number;
  micro_colony_count: number;
  largest_cluster_pct: number;
  clustered_biomass_pct: number;
  pattern: 'dense_clusters' | 'micro_colonies' | 'scattered';
  pattern_text: string;
  live_pct: number | null;
  matrix_pct: number | null;
  overlay_png: string;
  indicator: number;
}

export interface SpectrumEvidence {
  range_cm: [number, number];
  points: number;
  snr: number;
  quality: 'good' | 'fair' | 'poor';
  peaks: { wavenumber: number; intensity: number; assignment: string }[];
  matrix_ratio: number | null;
  matrix_level: 'strong' | 'moderate' | 'weak' | 'unknown';
  matrix_text: string;
  indicator: number | null;
  trace: [number, number][];
}

export interface GenomicModelResult {
  status: 'completed' | 'out_of_scope' | 'unavailable';
  predicted_class?: 'pathogenic' | 'commensal';
  probability_pathogenic?: number;
  reasons?: string[];
}

export interface GenomeEvidence {
  length_bp: number;
  contigs: number;
  n50_bp: number;
  gc_pct: number;
  markers: { gene: string; role: string; present: boolean; coverage_pct: number; closest_reference: string }[];
  mecA: boolean;
  ica_operon: boolean;
  indicator: number | null;
  genomic_model: GenomicModelResult;
}

export interface ClinicalEvidence {
  factors: { factor: string; present: boolean; why: string }[];
  present_count: number;
  total: number;
  indicator: number;
}

export interface Evidence {
  microscopy?: MicroscopyEvidence | { error: string };
  spectroscopy?: SpectrumEvidence | { error: string };
  genomics?: GenomeEvidence | { error: string };
  clinical?: ClinicalEvidence;
}

export interface ScorePart {
  modality: ModalityName;
  label: string;
  indicator: number;
  weight: number;
}

export interface AnalysisResponse {
  analysisId: string;
  sampleId?: string;
  status: AnalysisStatus;
  createdAt: string;
  completedAt?: string;
  prediction?: PredictionResult;
  modalities?: {
    microscopy?: ModalityRepresentation;
    spectroscopy?: ModalityRepresentation;
    genomics?: ModalityRepresentation;
    clinical?: ModalityRepresentation;
  };
  interpretation?: {
    microscopyAttention?: {
      originalAvailable: boolean;
      overlayAvailable: boolean;
      heatmapAvailable: boolean;
    };
    crossAttention?: CrossAttentionMap;
  };
  evidence?: Evidence;
  findings?: string[];
  scoreBreakdown?: ScorePart[];
  demoMode?: boolean;
  modelMode?: string;
  message?: string;
}

export interface AnalysisRequest {
  sampleInfo: SampleInfo;
  clinicalData: ClinicalData;
  microscopyFile?: File;
  spectroscopyFile?: File;
  genomicsFile?: File;
}

export interface AnalysisSummary {
  analysisId: string;
  sampleId: string;
  sampleType: string;
  createdAt: string;
  modalities: ModalityName[];
  prediction?: PredictionResult;
  status: AnalysisStatus;
  demoMode?: boolean;
}

export interface ProcessingStep {
  id: string;
  label: string;
  status: 'complete' | 'active' | 'pending';
}
