import Link from 'next/link';
import { Logo } from './Logo';

export function Footer() {
  const year = new Date().getFullYear();
  return (
    <footer className="border-t border-border bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          <div className="col-span-2">
            <Logo size="md" />
            <p className="mt-4 text-sm text-ink-secondary max-w-sm leading-relaxed">
              A research prototype for multimodal prediction of biofilm-associated infection.
              Outputs are computational and intended for research use only.
            </p>
            <p className="mt-4 text-[11px] text-ink-secondary leading-relaxed">
              BiofilmAI is a research prototype. Outputs are computational predictions and
              are not intended to diagnose, treat, or rule out disease. Results should not
              replace laboratory testing or professional clinical judgment.
            </p>
          </div>

          <div>
            <h4 className="text-[12px] font-semibold uppercase tracking-wider text-ink-secondary mb-3">
              Platform
            </h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/dashboard" className="text-ink hover:text-primary">Dashboard</Link></li>
              <li><Link href="/analyze" className="text-ink hover:text-primary">New Analysis</Link></li>
              <li><Link href="/history" className="text-ink hover:text-primary">History</Link></li>
            </ul>
          </div>

          <div>
            <h4 className="text-[12px] font-semibold uppercase tracking-wider text-ink-secondary mb-3">
              Resources
            </h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/about" className="text-ink hover:text-primary">About</Link></li>
              <li><Link href="/settings" className="text-ink hover:text-primary">Settings</Link></li>
            </ul>
          </div>
        </div>

        <div className="mt-10 pt-6 border-t border-border-subtle flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-ink-secondary">
          <span>© {year} BiofilmAI</span>
        </div>
      </div>
    </footer>
  );
}
