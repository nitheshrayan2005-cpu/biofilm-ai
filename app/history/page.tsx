'use client';

import { useState, useMemo, useEffect } from 'react';
import Link from 'next/link';
import { Search, FileSpreadsheet } from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Input, Select } from '@/components/ui/Input';
import { EmptyState } from '@/components/ui/Modal';
import { getAnalysisHistory } from '@/lib/api';
import { formatDateTime } from '@/lib/utils';
import { AnalysisSummary, ModalityName } from '@/lib/types';

export default function HistoryPage() {
  const [search, setSearch] = useState('');
  const [risk, setRisk] = useState('all');
  const [type, setType] = useState('all');
  const [status, setStatus] = useState('all');
  const [history, setHistory] = useState<AnalysisSummary[]>([]);
  const [loading, setLoading] = useState(false);

  // Load history from backend on mount
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getAnalysisHistory()
      .then((data) => {
        if (!cancelled) setHistory(data);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const filtered = useMemo(() => {
    return history.filter((row) => {
      if (search && !`${row.analysisId} ${row.sampleId} ${row.sampleType}`.toLowerCase().includes(search.toLowerCase())) return false;
      if (risk !== 'all' && row.prediction?.riskCategory !== risk) return false;
      if (type !== 'all' && row.sampleType !== type) return false;
      if (status !== 'all' && row.status !== status) return false;
      return true;
    });
  }, [search, risk, type, status, history]);

  const allTypes = Array.from(new Set(history.map((h) => h.sampleType)));

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
        <div>
          <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">Analysis History</p>
          <h1 className="mt-2 text-2xl sm:text-3xl font-semibold text-ink">All multimodal analyses</h1>
          <p className="mt-1.5 text-sm text-ink-secondary">Browse, filter, and review prior research outputs.</p>
        </div>
      </div>

      <Card padding="md" className="mb-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div className="lg:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-secondary" />
              <Input
                placeholder="Search by ID, sample, or type…"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>
          <Select
            options={[
              { value: 'all', label: 'All risk categories' },
              { value: 'low', label: 'Low' },
              { value: 'intermediate', label: 'Intermediate' },
              { value: 'high', label: 'High' },
            ]}
            value={risk}
            onChange={(e) => setRisk(e.target.value)}
          />
          <Select
            options={[
              { value: 'all', label: 'All sample types' },
              ...allTypes.map((t) => ({ value: t, label: t })),
            ]}
            value={type}
            onChange={(e) => setType(e.target.value)}
          />
          <Select
              options={[
                { value: 'all', label: 'All statuses' },
                { value: 'completed', label: 'Completed' },
                { value: 'processing', label: 'Processing' },
                { value: 'failed', label: 'Failed' },
                { value: 'draft', label: 'Draft' },
              ]}
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            />
        </div>
      </Card>

      {filtered.length === 0 ? (
        <EmptyState
          icon={<FileSpreadsheet className="h-6 w-6" />}
          title={history.length ? 'No analyses match these filters' : 'No analyses yet'}
          description={history.length ? 'Try clearing one or more filters.' : 'Run an analysis and it will appear here.'}
          action={<Link href="/analyze"><Button>Start Analysis</Button></Link>}
        />
      ) : (
        <Card padding="md">
          <CardHeader className="mb-3">
            <CardTitle>{filtered.length} analyses</CardTitle>
            <p className="text-xs text-ink-secondary">Showing latest first</p>
          </CardHeader>

          <div className="-mx-5 overflow-x-auto">
            <table className="w-full text-sm min-w-[800px]">
              <thead>
                <tr className="border-t border-b border-border-subtle bg-surface-muted/50">
                  <Th>Analysis ID</Th>
                  <Th>Sample ID</Th>
                  <Th>Type</Th>
                  <Th>Modalities</Th>
                  <Th>Score</Th>
                  <Th>Risk</Th>
                  <Th>Status</Th>
                  <Th>Created</Th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((row) => (
                  <HistoryRow key={row.analysisId} row={row} />
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}

function HistoryRow({ row }: { row: AnalysisSummary }) {
  const accent =
    row.prediction?.riskCategory === 'high'
      ? 'danger'
      : row.prediction?.riskCategory === 'intermediate'
      ? 'warning'
      : 'success';
  return (
    <tr className="border-b border-border-subtle/60 hover:bg-surface-muted/40 transition-colors">
      <Td mono>{row.analysisId}</Td>
      <Td mono>{row.sampleId}</Td>
      <Td>{row.sampleType}</Td>
      <Td>
        <div className="flex flex-wrap gap-1">
          {row.modalities.map((m) => (
            <Badge key={m} variant="info" size="sm">
              {m}
            </Badge>
          ))}
        </div>
      </Td>
      <Td className="font-mono">
        {row.prediction ? `${(row.prediction.biofilmProbability * 100).toFixed(1)}%` : '—'}
      </Td>
      <Td>
        {row.prediction && (
          <Badge variant={accent as any} size="sm" dot>
            {row.prediction.riskCategory}
          </Badge>
        )}
      </Td>
      <Td>
        <StatusBadge status={row.status} />
      </Td>
      <Td className="text-ink-secondary">{formatDateTime(row.createdAt)}</Td>
    </tr>
  );
}

function StatusBadge({ status }: { status: string }) {
  if (status === 'completed') return <Badge variant="success" size="sm" dot>Completed</Badge>;
  if (status === 'processing') return <Badge variant="info" size="sm" dot>Processing</Badge>;
  if (status === 'failed') return <Badge variant="danger" size="sm" dot>Failed</Badge>;
  return <Badge variant="neutral" size="sm" dot>Draft</Badge>;
}

function Th({ children, className }: { children?: React.ReactNode; className?: string }) {
  return (
    <th className={`text-left px-5 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-ink-secondary ${className || ''}`}>
      {children}
    </th>
  );
}
function Td({ children, mono, className }: { children?: React.ReactNode; mono?: boolean; className?: string }) {
  return (
    <td className={`px-5 py-3 text-sm text-ink ${mono ? 'font-mono text-[12px]' : ''} ${className || ''}`}>{children}</td>
  );
}
