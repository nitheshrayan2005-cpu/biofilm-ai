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
