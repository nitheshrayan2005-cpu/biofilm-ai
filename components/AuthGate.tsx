'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Doctor, getDoctor, isPublicPath, onAuthChange } from '@/lib/auth';
import { verifySession } from '@/lib/api';

/** The signed-in doctor, updated on sign-in and sign-out. */
export function useDoctor(): Doctor | null {
  const [doctor, setDoctor] = useState<Doctor | null>(null);
  useEffect(() => {
    setDoctor(getDoctor());
    return onAuthChange(() => setDoctor(getDoctor()));
  }, []);
  return doctor;
}

/** Sends signed-out visitors on protected pages to /login. */
export function AuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const isPublic = isPublicPath(pathname);
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    if (isPublic) {
      setAllowed(true);
      return;
    }
    let cancelled = false;
    setAllowed(false);
    verifySession().then((ok) => {
      if (cancelled) return;
      if (ok) setAllowed(true);
      else router.replace(`/login?next=${encodeURIComponent(pathname)}`);
    });
    return () => {
      cancelled = true;
    };
  }, [pathname, isPublic, router]);

  if (!isPublic && !allowed) return null;
  return <>{children}</>;
}
