// Doctor sign-in state. The backend issues a signed token on login; it is
// kept in localStorage and sent as a Bearer token on every API request.

export interface Doctor {
  username: string;
  name: string;
}

interface Session {
  token: string;
  doctor: Doctor;
}

const STORAGE_KEY = 'biofilm-auth';
const AUTH_EVENT = 'biofilm-auth-change';

// Pages anyone can open without signing in.
export const PUBLIC_PATHS = ['/', '/login', '/welcome', '/about', '/research'];

export function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.includes(pathname);
}

export function getSession(): Session | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null;
  }
}

export function getToken(): string | null {
  return getSession()?.token ?? null;
}

export function getDoctor(): Doctor | null {
  return getSession()?.doctor ?? null;
}

export function saveSession(session: Session) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  } catch {}
  window.dispatchEvent(new Event(AUTH_EVENT));
}

export function clearSession() {
  try {
    localStorage.removeItem(STORAGE_KEY);
    sessionStorage.removeItem('biofilm-last-result');
    sessionStorage.removeItem('biofilm-last-request');
  } catch {}
  window.dispatchEvent(new Event(AUTH_EVENT));
}

export function onAuthChange(callback: () => void) {
  window.addEventListener(AUTH_EVENT, callback);
  window.addEventListener('storage', callback);
  return () => {
    window.removeEventListener(AUTH_EVENT, callback);
    window.removeEventListener('storage', callback);
  };
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part[0]!.toUpperCase())
    .slice(0, 2)
    .join('') || 'DR';
}
