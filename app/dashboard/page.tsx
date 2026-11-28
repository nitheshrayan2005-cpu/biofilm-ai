'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from 'recharts';
import {
  TrendingUp,
  Activity,
  AlertTriangle,
  Clock,
  ArrowRight,
  FileBarChart2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { StatusBanner } from '@/components/ui/Modal';
import { AnalysisSummary } from '@/lib/types';
import { getAnalysisHistory } from '@/lib/api';
import { formatRelative } from '@/lib/utils';
import { useDoctor } from '@/components/AuthGate';

export default function DashboardPage() {
  const doctor = useDoctor();
  const [mounted, setMounted] = useState(false);
  const [history, setHistory] = useState<AnalysisSummary[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setMounted(true);
    // Load real history from backend
    setLoading(true);
    getAnalysisHistory()
      .then((data) => setHistory(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const series = mounted ? activitySeries(history) : [];
  const total = history.length;
  const high = history.filter((h) => h.prediction?.riskCategory === 'high').length;
  const avgConfidence = history.length
    ? Math.round(
        (history.reduce((acc, h) => acc + (h.prediction?.biofilmProbability ?? 0), 0) /
          history.length) *
          100
      )
    : 0;
  const weekAgo = Date.now() - 7 * 24 * 3600 * 1000;
  const lastWeek = history.filter((h) => new Date(h.createdAt).getTime() >= weekAgo).length;
  const recent = [...history]
    .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    .slice(0, 6);

  const distribution = [
    { name: 'Low', value: history.filter((h) => h.prediction?.riskCategory === 'low').length, color: '#2E8B72' },
    { name: 'Intermediate', value: history.filter((h) => h.prediction?.riskCategory === 'intermediate').length, color: '#D99A2B' },
    { name: 'High', value: history.filter((h) => h.prediction?.riskCategory === 'high').length, color: '#C94C4C' },
  ];

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
      <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-8">
        <div>
          <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">Dashboard</p>
          <h1 className="mt-2 text-2xl sm:text-3xl font-semibold text-ink">Welcome{doctor ? `, ${doctor.name}` : ''}</h1>
          <p className="mt-1.5 text-sm text-ink-secondary">
            Review multimodal analyses and monitor your research workflow.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/analyze">
            <Button size="sm" iconRight={<ArrowRight className="h-4 w-4" />}>New Analysis</Button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <MetricCard
          icon={FileBarChart2}
          label="Total Analyses"
          value={total.toString()}
          sub="All saved analyses"
          accent="primary"
        />
        <MetricCard
          icon={AlertTriangle}
          label="High-Risk Results"
          value={high.toString()}
          sub={`${Math.round((high / total) * 100) || 0}% of total`}
          accent="danger"
        />
        <MetricCard
          icon={TrendingUp}
          label="Average Score"
          value={`${avgConfidence}%`}
          sub="Mean evidence score"
          accent="secondary"
        />
        <MetricCard
          icon={Clock}
          label="Recent Activity"
          value={lastWeek.toString()}
          sub="Analyses in the last 7 days"
          accent="warning"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 mb-8">
        <Card className="lg:col-span-2">
          <CardHeader>
            <div>
              <CardTitle>Analysis Activity</CardTitle>
              <CardDescription>Number of analyses performed over the past two weeks.</CardDescription>
            </div>
          </CardHeader>
          <div className="h-72 mt-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={series} margin={{ top: 10, right: 12, left: -20, bottom: 0 }}>
                <CartesianGrid stroke="#EBF1F4" strokeDasharray="0" vertical={false} />
                <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#607784' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 11, fill: '#607784' }} axisLine={false} tickLine={false} />
                <Tooltip
                  contentStyle={{
                    borderRadius: 8,
                    border: '1px solid #DCE7EC',
                    boxShadow: '0 4px 12px rgba(18,48,71,0.06)',
                    fontSize: 12,
                  }}
                />
                <Line type="monotone" dataKey="analyses" stroke="#176B87" strokeWidth={2.5} dot={{ r: 3, fill: '#176B87' }} activeDot={{ r: 6 }} isAnimationActive={false} />
                <Line type="monotone" dataKey="high" stroke="#C94C4C" strokeWidth={2} dot={false} strokeDasharray="4 4" isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <CardHeader>
            <div>
              <CardTitle>Risk Distribution</CardTitle>
              <CardDescription>Risk categories of all saved analyses.</CardDescription>
            </div>
          </CardHeader>
          <div className="h-72 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={distribution}
                  innerRadius={56}
                  outerRadius={88}
                  paddingAngle={3}
                  dataKey="value"
                  stroke="none"
                  isAnimationActive={false}
                >
                  {distribution.map((d, i) => (
                    <Cell key={i} fill={d.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    borderRadius: 8,
                    border: '1px solid #DCE7EC',
                    fontSize: 12,
                  }}
                />
                <Legend
                  verticalAlign="bottom"
                  iconType="circle"
                  wrapperStyle={{ fontSize: 12, color: '#607784' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <div>
            <CardTitle>Recent Analyses</CardTitle>
            <CardDescription>Latest multimodal research outputs from your workflow.</CardDescription>
          </div>
          <div className="flex gap-2">
            <Link href="/history">
              <Button size="sm" variant="outline" iconRight={<ArrowRight className="h-4 w-4" />}>View all</Button>
            </Link>
          </div>
        </CardHeader>

        <div className="-mx-5 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-t border-b border-border-subtle bg-surface-muted/50">
                <Th>Analysis ID</Th>
                <Th>Sample</Th>
                <Th>Type</Th>
                <Th>Modalities</Th>
                <Th>Score</Th>
                <Th>Status</Th>
                <Th>When</Th>
              </tr>
            </thead>
            <tbody>
              {recent.length === 0 && (
                <tr>
                  <td colSpan={7} className="px-5 py-8 text-center text-sm text-ink-secondary">
                    No analyses yet. <Link href="/analyze" className="text-primary font-medium">Run your first analysis</Link>.
                  </td>
                </tr>
              )}
              {recent.map((row) => (
                <tr key={row.analysisId} className="border-b border-border-subtle/60 hover:bg-surface-muted/40">
                  <Td mono>{row.analysisId}</Td>
                  <Td mono>{row.sampleId}</Td>
                  <Td>{row.sampleType}</Td>
                  <Td>
                    <div className="flex flex-wrap gap-1">
                      {row.modalities.map((m) => (
                        <Badge key={m} size="sm" variant="info">
                          {m}
                        </Badge>
                      ))}
                    </div>
                  </Td>
                  <Td>
                    {row.prediction && (
                      <RiskPill
                        probability={row.prediction.biofilmProbability}
                        category={row.prediction.riskCategory}
                      />
                    )}
                  </Td>
                  <Td><Badge variant="success" size="sm" dot>Completed</Badge></Td>
                  <Td className="text-ink-secondary">{formatRelative(row.createdAt)}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

    </div>
  );
}

// Analyses and high-risk results per day over the last 14 days.
function activitySeries(history: AnalysisSummary[]) {
  const days = [...Array(14)].map((_, i) => {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    d.setDate(d.getDate() - (13 - i));
    return d;
  });
  return days.map((d) => {
    const same = history.filter((h) => new Date(h.createdAt).toDateString() === d.toDateString());
    return {
      date: `${d.getDate()}/${d.getMonth() + 1}`,
      analyses: same.length,
      high: same.filter((h) => h.prediction?.riskCategory === 'high').length,
    };
  });
}

function MetricCard({ icon: Icon, label, value, sub, accent }: any) {
  const accentMap: any = {
    primary: 'bg-primary-50 text-primary',
    secondary: 'bg-secondary-50 text-secondary',
    danger: 'bg-danger-50 text-danger',
    warning: 'bg-warning-50 text-warning',
  };
  return (
    <Card padding="md" className="hover:shadow-soft transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1.5">
          <p className="text-[12px] font-medium text-ink-secondary">{label}</p>
          <p className="text-2xl font-semibold text-ink leading-none">{value}</p>
          <p className="text-[11px] text-ink-secondary">{sub}</p>
        </div>
        <div className={`h-9 w-9 rounded-md flex items-center justify-center ${accentMap[accent]}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
    </Card>
  );
}

function Th({ children }: { children?: React.ReactNode }) {
  return (
    <th className="text-left px-5 py-2.5 text-[11px] font-semibold uppercase tracking-wider text-ink-secondary">
      {children}
    </th>
  );
}
function Td({ children, mono, className }: { children?: React.ReactNode; mono?: boolean; className?: string }) {
  return (
    <td className={`px-5 py-3 text-sm text-ink ${mono ? 'font-mono text-[12px]' : ''} ${className || ''}`}>{children}</td>
  );
}

function RiskPill({ probability, category }: { probability: number; category: string }) {
  const variant = category === 'high' ? 'danger' : category === 'intermediate' ? 'warning' : 'success';
  return (
    <div className="flex items-center gap-2">
      <span className="font-mono text-[12px] w-10">{(probability * 100).toFixed(0)}%</span>
      <Badge variant={variant} size="sm" dot>
        {category}
      </Badge>
    </div>
  );
}
