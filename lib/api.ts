// BiofilmAI API service — Backend integration layer.
//
// This module provides the interface between the frontend and the
// FastAPI backend. When the backend is available, real requests are
// made; otherwise fallback to demo/mock data.
//
// Backend endpoints:
//   POST /api/analyze           — Run a multimodal analysis
//   GET  /api/history           — List all analyses
//   GET  /api/analysis/{id}     — Get a single analysis
//   GET  /api/health            — Health check
//   POST /api/auth/login        — Doctor sign-in (all other routes need the token)
//
// To switch to production mode, change BACKEND_READY to true
// and update BACKEND_URL.

import {
  AnalysisRequest,
  AnalysisResponse,
  AnalysisSummary,
  RiskCategory,
  ModalityName,
} from './types';
import {
  MOCK_HISTORY,
  generateMockAnalysis,
  generateMockAttentionMap,
} from './mockData';
import { getToken, clearSession, saveSession, Doctor } from './auth';

// ── Configuration ──────────────────────────────────────────────────────────

// Set this to true when the backend is running.
export const BACKEND_READY = true;

// Backend URL resolution
//
// By default requests go to the site's own /api/*, which next.config.js
// forwards to the backend, so it works from any host the page is opened on.
// Set `NEXT_PUBLIC_BACKEND_URL` only to call a backend directly instead.
export const BACKEND_URL = (process.env.NEXT_PUBLIC_BACKEND_URL ?? '').trim().replace(/\/$/, '');

// When backend is ready, demo mode is still true (the backend uses demo inference).
// When the real model is integrated, this should be set to false.
export const DEMO_MODE = true;

// ── Auth ───────────────────────────────────────────────────────────────────

/** fetch() with the doctor's token attached. A 401 signs the doctor out. */
async function authFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);
  const res = await fetch(`${BACKEND_URL}${path}`, { ...init, headers });
  if (res.status === 401 && typeof window !== 'undefined') {
    clearSession();
    window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
  }
  return res;
}

/** Sign in a doctor and store the session. */
export async function login(username: string, password: string): Promise<Doctor> {
  const res = await fetch(`${BACKEND_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.detail || body.message || 'Sign-in failed');
  saveSession({ token: body.token, doctor: body.doctor });
  return body.doctor;
}

/** Check the stored token is still valid. Returns false if the doctor must sign in again. */
export async function verifySession(): Promise<boolean> {
  if (!getToken()) return false;
  try {
    const res = await authFetch('/api/auth/me');
    return res.ok;
  } catch {
    // Backend unreachable: keep the session, API calls will report the error.
    return true;
  }
}

// ── Public API ─────────────────────────────────────────────────────────────

/**
 * Run a multimodal analysis.
 *
 * If the backend is available, this makes a real HTTP request to
 * POST /api/analyze.  Otherwise, it falls back to mock data.
 *
 * @param request - The analysis request containing sample info, clinical data, and files.
 * @returns AnalysisResponse with prediction, modalities, and interpretation.
 */
export async function analyze(request: AnalysisRequest): Promise<AnalysisResponse> {
  if (!BACKEND_READY) {
    // Mock mode — simulate processing time
    await delay(1800);
    return generateMockAnalysis(request);
  }

  // Build the multipart form data for the real backend
  const formData = new FormData();

  // Include sample info and clinical data as JSON strings
  formData.append('sampleInfo', JSON.stringify(request.sampleInfo));
  formData.append('clinicalData', JSON.stringify(request.clinicalData));

  // Include file uploads (if any)
  if (request.microscopyFile) {
    formData.append('microscopy', request.microscopyFile);
  }
  if (request.spectroscopyFile) {
    formData.append('spectroscopy', request.spectroscopyFile);
  }
  if (request.genomicsFile) {
    formData.append('genomics', request.genomicsFile);
  }

  const res = await authFetch('/api/analyze', {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorBody = await res.json().catch(() => ({ message: 'Analysis failed' }));
    throw new Error(errorBody.message || errorBody.detail || `Analysis request failed with status ${res.status}`);
  }

  return res.json();
}

/**
 * Get the list of all analyses (history).
 */
export async function getAnalysisHistory(): Promise<AnalysisSummary[]> {
  if (!BACKEND_READY) {
    await delay(120);
    return MOCK_HISTORY;
  }

  const res = await authFetch('/api/history');
  if (!res.ok) throw new Error('Failed to load analyses');
  return res.json();
}

/**
 * Get a single analysis by ID.
 */
export async function getAnalysis(id: string): Promise<AnalysisResponse | null> {
  if (!BACKEND_READY) {
    await delay(150);
    const found = MOCK_HISTORY.find((a) => a.analysisId === id);
    if (!found) return null;
    return buildResponseFromSummary(found);
  }

  const res = await authFetch(`/api/analysis/${encodeURIComponent(id)}`);
  if (!res.ok) return null;
  return res.json();
}

/**
 * Get the cross-attention map (for visualization).
 */
export async function getCrossAttentionMap() {
  if (!BACKEND_READY) return generateMockAttentionMap();
  const res = await authFetch('/api/visualizations/cross-attention');
  if (!res.ok) return null;
  return res.json();
}

/**
 * Health check — verify the backend is available.
 */
export async function checkHealth(): Promise<{ status: string; version: string; demoMode: boolean } | null> {
  if (!BACKEND_READY) return null;
  try {
    const res = await fetch(`${BACKEND_URL}/api/health`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function buildResponseFromSummary(s: AnalysisSummary): AnalysisResponse {
  const probability = s.prediction?.biofilmProbability ?? 0.5;
  return {
    analysisId: s.analysisId,
    status: s.status,
    createdAt: s.createdAt,
    completedAt: s.createdAt,
    prediction: s.prediction,
    modalities: {
      microscopy: { modality: 'microscopy', available: true, status: 'available' },
      spectroscopy: { modality: 'spectroscopy', available: true, status: 'available' },
      genomics: { modality: 'genomics', available: true, status: 'available' },
      clinical: { modality: 'clinical', available: true, status: 'available' },
    },
    interpretation: {
      crossAttention: generateMockAttentionMap(),
    },
    demoMode: DEMO_MODE,
  };
}

/**
 * Risk classification helper.
 */
export function classifyRisk(probability: number): RiskCategory {
  if (probability < 0.4) return 'low';
  if (probability < 0.7) return 'intermediate';
  return 'high';
}

/**
 * Extract modalities from an AnalysisRequest.
 */
export function modalitiesFromRequest(request: AnalysisRequest): ModalityName[] {
  const list: ModalityName[] = [];
  if (request.microscopyFile) list.push('microscopy');
  if (request.spectroscopyFile) list.push('spectroscopy');
  if (request.genomicsFile) list.push('genomics');
  if (request.clinicalData) list.push('clinical');
  return list;
}