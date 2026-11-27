'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { Menu, X, User, Settings, LogOut, FlaskConical } from 'lucide-react';
import { Logo } from './Logo';
import { Button } from '@/components/ui/Button';
import { cn } from '@/lib/utils';
import { useDoctor } from '@/components/AuthGate';
import { LOGIN_REQUIRED, clearSession, initials } from '@/lib/auth';

const navLinks = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/analyze', label: 'Analyze Sample' },
  { href: '/history', label: 'History' },
  { href: '/about', label: 'About' },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const doctor = useDoctor();
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 6);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    setOpen(false);
    setMenuOpen(false);
  }, [pathname]);

  function signOut() {
    clearSession();
    router.replace('/login');
  }

  // Hide navbar on the landing and sign-in pages (they have their own hero)
  if (pathname === '/' || pathname === '/login' || pathname === '/welcome') return null;

  return (
    <header
      className={cn(
        'sticky top-0 z-30 backdrop-blur transition-all duration-200',
        scrolled
          ? 'bg-white/85 border-b border-border shadow-[0_1px_0_rgba(18,48,71,0.04)]'
          : 'bg-white/70 border-b border-transparent'
      )}
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between gap-4">
          <Link href="/dashboard" className="flex items-center gap-2 shrink-0">
            <Logo size="md" withSubtitle />
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const active = pathname.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                    active
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-ink-secondary hover:text-ink hover:bg-surface-muted'
                  )}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center gap-1.5">
            <Link href="/analyze" className="hidden sm:inline-flex">
              <Button size="sm" iconLeft={<FlaskConical className="h-4 w-4" />}>
                New Analysis
              </Button>
            </Link>

            {!doctor && (
              <Link href="/login" className="hidden sm:inline-flex">
                <Button size="sm" variant="outline">Sign in</Button>
              </Link>
            )}

            {doctor && (
            <div className="relative hidden sm:block">
              <button
                type="button"
                onClick={() => setMenuOpen((v) => !v)}
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                className="inline-flex items-center gap-2 h-9 pl-1.5 pr-2 rounded-md text-ink-secondary hover:bg-surface-muted focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-300"
              >
                <div className="h-7 w-7 rounded-full bg-gradient-to-br from-primary-200 to-secondary/40 flex items-center justify-center text-[11px] font-semibold text-primary-700">
                  {initials(doctor.name)}
                </div>
                <span className="text-[13px] font-medium">{doctor.name}</span>
              </button>
              {menuOpen && (
                <div
                  role="menu"
                  className="absolute right-0 mt-2 w-56 rounded-lg border border-border bg-white shadow-lifted py-1 animate-fade-in"
                >
                  <div className="px-3 py-2 border-b border-border-subtle">
                    <p className="text-[13px] font-medium text-ink">{doctor.name}</p>
                    <p className="text-xs text-ink-secondary">@{doctor.username}</p>
                  </div>
                  <Link href="/settings" className="flex items-center gap-2 px-3 py-2 text-sm text-ink hover:bg-surface-muted">
                    <User className="h-4 w-4 text-ink-secondary" /> Profile
                  </Link>
                  <Link href="/settings" className="flex items-center gap-2 px-3 py-2 text-sm text-ink hover:bg-surface-muted">
                    <Settings className="h-4 w-4 text-ink-secondary" /> Settings
                  </Link>
                  {LOGIN_REQUIRED && (
                    <>
                      <div className="border-t border-border-subtle my-1" />
                      <button
                        type="button"
                        onClick={signOut}
                        className="w-full flex items-center gap-2 px-3 py-2 text-sm text-ink hover:bg-surface-muted"
                      >
                        <LogOut className="h-4 w-4 text-ink-secondary" /> Sign out
                      </button>
                    </>
                  )}
                </div>
              )}
            </div>
            )}

            <button
              type="button"
              className="md:hidden h-9 w-9 inline-flex items-center justify-center rounded-md text-ink-secondary hover:bg-surface-muted hover:text-ink"
              aria-label="Toggle menu"
              onClick={() => setOpen((v) => !v)}
            >
              {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile sheet */}
      {open && (
        <div className="md:hidden border-t border-border bg-white animate-fade-in">
          <nav className="px-4 py-3 flex flex-col gap-1">
            {navLinks.map((link) => {
              const active = pathname.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    active
                      ? 'bg-primary-50 text-primary-700'
                      : 'text-ink hover:bg-surface-muted'
                  )}
                >
                  {link.label}
                </Link>
              );
            })}
            <Link href="/analyze" className="mt-2">
              <Button size="md" fullWidth iconLeft={<FlaskConical className="h-4 w-4" />}>
                New Analysis
              </Button>
            </Link>
            {doctor ? (
              <>
                <Link href="/settings" className="px-3 py-2 text-sm text-ink">
                  <span className="inline-flex items-center gap-2">
                    <User className="h-4 w-4" /> {doctor.name} · Settings
                  </span>
                </Link>
                {LOGIN_REQUIRED && (
                  <button type="button" onClick={signOut} className="px-3 py-2 text-sm text-ink text-left">
                    <span className="inline-flex items-center gap-2">
                      <LogOut className="h-4 w-4" /> Sign out
                    </span>
                  </button>
                )}
              </>
            ) : (
              <Link href="/login" className="px-3 py-2 text-sm text-ink">
                <span className="inline-flex items-center gap-2">
                  <User className="h-4 w-4" /> Sign in
                </span>
              </Link>
            )}
          </nav>
        </div>
      )}
    </header>
  );
}
