'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getToken } from '@/lib/auth';

// The site opens on sign-in; signed-in doctors go straight to a new analysis.
export default function RootPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace(getToken() ? '/analyze' : '/login');
  }, [router]);
  return null;
}
