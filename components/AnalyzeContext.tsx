'use client';

import { createContext, useContext, useState, ReactNode } from 'react';
import { ClinicalData, SampleInfo } from '@/lib/types';

export interface AnalyzeState {
  step: number;
  sampleInfo: SampleInfo;
  clinicalData: ClinicalData;
  microscopyFile: File | null;
  microscopyPreview: string | null;
  spectroscopyFile: File | null;
  spectroscopyPreview: any[] | null;
  genomicsFile: File | null;
  genomicsFileName: string | null;
  genomicsFormat: 'fasta' | 'csv' | 'txt' | 'unknown' | null;
}

const defaultSampleInfo: SampleInfo = {
  sampleId: '',
  studyId: '',
  sampleType: '',
  collectionDate: '',
  infectionContext: '',
  woundOrImplant: '',
  notes: '',
};

const defaultClinicalData: ClinicalData = {
  infectionContext: '',
  chronicityDays: 0,
  implantPresent: false,
  sampleSite: '',
  previousTreatment: '',
  previousCulture: '',
  additionalNotes: '',
};

const initialState: AnalyzeState = {
  step: 0,
  sampleInfo: defaultSampleInfo,
  clinicalData: defaultClinicalData,
  microscopyFile: null,
  microscopyPreview: null,
  spectroscopyFile: null,
  spectroscopyPreview: null,
  genomicsFile: null,
  genomicsFileName: null,
  genomicsFormat: null,
};

interface ContextValue {
  state: AnalyzeState;
  setStep: (n: number) => void;
  setSampleInfo: (v: SampleInfo) => void;
  setClinicalData: (v: ClinicalData) => void;
  setMicroscopyFile: (f: File | null, preview?: string | null) => void;
  setSpectroscopyFile: (f: File | null, data?: any[] | null) => void;
  setGenomicsFile: (f: File | null, name?: string | null, format?: any) => void;
  reset: () => void;
}

const AnalyzeContext = createContext<ContextValue | null>(null);

export function AnalyzeProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AnalyzeState>(initialState);

  const value: ContextValue = {
    state,
    setStep: (n) => setState((s) => ({ ...s, step: n })),
    setSampleInfo: (v) => setState((s) => ({ ...s, sampleInfo: v })),
    setClinicalData: (v) => setState((s) => ({ ...s, clinicalData: v })),
    setMicroscopyFile: (file, preview = null) =>
      setState((s) => ({ ...s, microscopyFile: file, microscopyPreview: preview })),
    setSpectroscopyFile: (file, data = null) =>
      setState((s) => ({ ...s, spectroscopyFile: file, spectroscopyPreview: data })),
    setGenomicsFile: (file, name = null, format: any = null) =>
      setState((s) => ({ ...s, genomicsFile: file, genomicsFileName: name, genomicsFormat: format })),
    reset: () => setState(initialState),
  };

  return <AnalyzeContext.Provider value={value}>{children}</AnalyzeContext.Provider>;
}

export function useAnalyze() {
  const ctx = useContext(AnalyzeContext);
  if (!ctx) throw new Error('useAnalyze must be used inside AnalyzeProvider');
  return ctx;
}

export const STEPS = [
  { id: 'sample', label: 'Sample Information' },
  { id: 'microscopy', label: 'Microscopy' },
  { id: 'spectroscopy', label: 'Spectroscopy' },
  { id: 'genomics', label: 'Genomics' },
  { id: 'clinical', label: 'Clinical Data' },
  { id: 'review', label: 'Review & Analyze' },
];
