'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { LogIn, ShieldCheck } from 'lucide-react';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { StatusBanner } from '@/components/ui/Modal';
import { Logo } from '@/components/layout/Logo';
import { login } from '@/lib/api';
import { LOGIN_REQUIRED, getToken, isPublicPath } from '@/lib/auth';

function nextPath(): string {
  const next = new URLSearchParams(window.location.search).get('next') || '';
  // Only allow in-app paths, and don't bounce back to a public page.
  if (!next.startsWith('/') || next.startsWith('//') || isPublicPath(next)) return '/analyze';
  return next;
}

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!LOGIN_REQUIRED || getToken()) router.replace(nextPath());
  }, [router]);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(username, password);
      router.replace(nextPath());
    } catch (err: any) {
      setError(
        err instanceof TypeError
          ? 'Cannot reach the server. Please try again shortly.'
          : err?.message || 'Sign-in failed'
      );
      setSubmitting(false);
    }
  }

  return (
    <div className="relative overflow-hidden min-h-[calc(100vh-1px)]">
      <div className="absolute inset-0 diagram-grid opacity-30 pointer-events-none" />
      <div className="absolute top-0 left-0 right-0 h-[420px] bg-gradient-to-b from-primary-50/70 via-surface-muted to-transparent pointer-events-none" />
      <CellBackground />

      <div className="relative mx-auto max-w-md px-4 py-16 sm:py-24">
        <Link href="/welcome" className="flex justify-center mb-8 rise-in">
          <Logo size="lg" withSubtitle />
        </Link>

        <Card padding="lg" className="glow-border shadow-lifted rise-in" style={{ animationDelay: '120ms' }}>
          <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">Doctor sign-in</p>
          <h1 className="mt-2 text-2xl font-semibold text-ink">Welcome back</h1>
          <p className="mt-1.5 text-sm text-ink-secondary">
            Sign in with the account provided by your administrator.
          </p>

          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            <Input
              label="Username"
              autoComplete="username"
              autoFocus
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
            <Input
              label="Password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            {error && <StatusBanner variant="danger" description={error} />}

            <Button
              type="submit"
              size="lg"
              fullWidth
              loading={submitting}
              iconLeft={<LogIn className="h-4 w-4" />}
              className="btn-sheen"
            >
              Sign in
            </Button>
          </form>

          <p className="mt-6 pt-5 border-t border-border-subtle flex gap-2 text-xs text-ink-secondary leading-relaxed">
            <ShieldCheck className="h-4 w-4 text-secondary shrink-0" />
            Access is limited to registered doctors. Contact your administrator if you need an
            account or have forgotten your password.
          </p>
        </Card>
      </div>
    </div>
  );
}

// Bacteria-like cells drifting upward behind the sign-in card (fixed layout so
// server and client render the same markup).
const CELLS = [
  { left: 4, size: 14, dur: 22, delay: 0, c: 'bg-primary/25' },
  { left: 11, size: 8, dur: 17, delay: 6, c: 'bg-secondary/30' },
  { left: 18, size: 22, dur: 28, delay: 3, c: 'bg-primary-300/30' },
  { left: 26, size: 10, dur: 19, delay: 11, c: 'bg-secondary/25' },
  { left: 33, size: 6, dur: 15, delay: 2, c: 'bg-primary/30' },
  { left: 41, size: 16, dur: 25, delay: 9, c: 'bg-secondary-300/30' },
  { left: 57, size: 12, dur: 21, delay: 4, c: 'bg-primary/20' },
  { left: 64, size: 24, dur: 30, delay: 12, c: 'bg-primary-200/40' },
  { left: 71, size: 9, dur: 18, delay: 7, c: 'bg-secondary/30' },
  { left: 78, size: 14, dur: 23, delay: 1, c: 'bg-primary-300/30' },
  { left: 85, size: 7, dur: 16, delay: 10, c: 'bg-primary/25' },
  { left: 92, size: 18, dur: 26, delay: 5, c: 'bg-secondary-300/30' },
  { left: 48, size: 9, dur: 20, delay: 14, c: 'bg-primary/20' },
  { left: 22, size: 12, dur: 24, delay: 16, c: 'bg-secondary/20' },
];

function CellBackground() {
  return (
    <div aria-hidden className="absolute inset-0 pointer-events-none overflow-hidden">
      <div className="blob h-72 w-72 bg-primary-200/40 -top-16 -left-20" />
      <div className="blob h-80 w-80 bg-secondary-200/40 top-1/3 -right-24" style={{ animationDelay: '-6s' }} />
      <div className="blob h-64 w-64 bg-primary-100/60 bottom-0 left-1/3" style={{ animationDelay: '-12s' }} />
      {CELLS.map((cell, i) => (
        <span
          key={i}
          className={`cell-float ${cell.c}`}
          style={{
            left: `${cell.left}%`,
            bottom: '-40px',
            width: cell.size,
            height: cell.size,
            animationDuration: `${cell.dur}s`,
            animationDelay: `-${cell.delay}s`,
          }}
        />
      ))}
    </div>
  );
}
