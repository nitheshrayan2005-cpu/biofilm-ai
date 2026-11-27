'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { LOGIN_REQUIRED, getToken } from '@/lib/auth';

// The site opens on a new analysis (or on sign-in when login is required).
export default function RootPage() {
  const router = useRouter();
  useEffect(() => {
    router.replace(!LOGIN_REQUIRED || getToken() ? '/analyze' : '/login');
  }, [router]);
  return null;
}
