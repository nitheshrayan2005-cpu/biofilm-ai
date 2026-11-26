'use client';

import { useState } from 'react';
import { User, Database } from 'lucide-react';
import { Card, CardTitle, CardDescription, CardEyebrow } from '@/components/ui/Card';
import { Input, Toggle } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { useDoctor } from '@/components/AuthGate';
import { initials } from '@/lib/auth';

const sections = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'data', label: 'Data preferences', icon: Database },
];

export default function SettingsPage() {
  const [active, setActive] = useState('profile');
  const [prefs, setPrefs] = useState({
    autoSaveDrafts: true,
    persistHistory: true,
  });

  function toggle(key: keyof typeof prefs) {
    setPrefs({ ...prefs, [key]: !prefs[key] });
  }

  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8 sm:py-10">
      <div className="mb-8">
        <p className="text-[11px] font-semibold tracking-widest uppercase text-primary">Settings</p>
        <h1 className="mt-2 text-2xl sm:text-3xl font-semibold text-ink">Account settings</h1>
        <p className="mt-1.5 text-sm text-ink-secondary">
          Manage your profile and data preferences.
        </p>
      </div>

      <div className="grid lg:grid-cols-12 gap-6">
        <aside className="lg:col-span-3">
          <nav className="rounded-lg border border-border bg-white p-2 sticky top-24">
            {sections.map((sec) => {
              const isActive = active === sec.id;
              return (
                <button
                  key={sec.id}
                  onClick={() => setActive(sec.id)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive ? 'bg-primary-50 text-primary-700' : 'text-ink-secondary hover:bg-surface-muted hover:text-ink'
                  }`}
                >
                  <sec.icon className="h-4 w-4" />
                  {sec.label}
                </button>
              );
            })}
          </nav>
        </aside>

        <main className="lg:col-span-9 space-y-5">
          {active === 'profile' && <ProfileSection />}
          {active === 'data' && <DataSection prefs={prefs} toggle={toggle} />}
        </main>
      </div>
    </div>
  );
}

function ProfileSection() {
  const doctor = useDoctor();
  return (
    <div className="space-y-5 animate-fade-in">
      <Card padding="lg">
        <CardEyebrow>Profile</CardEyebrow>
        <CardTitle className="mt-1">Personal information</CardTitle>
        <CardDescription className="mt-1">
          Used to identify your research activity. Avoid sharing sensitive personal data.
        </CardDescription>

        <div className="mt-6 flex items-center gap-4">
          <div className="h-16 w-16 rounded-full bg-gradient-to-br from-primary-200 to-secondary/40 flex items-center justify-center text-base font-semibold text-primary-700">
            {doctor ? initials(doctor.name) : ''}
          </div>
        </div>

        <div className="mt-6 grid sm:grid-cols-2 gap-4">
          <Input label="Full name" key={doctor?.username} defaultValue={doctor?.name ?? ''} />
          <Input label="Research role" placeholder="e.g. Clinical microbiologist" />
          <Input label="Organization" placeholder="Hospital or institution" />
          <Input label="Email" type="email" placeholder="you@example.com" />
        </div>

        <div className="mt-6 flex gap-2">
          <Button>Save changes</Button>
          <Button variant="outline">Cancel</Button>
        </div>
      </Card>
    </div>
  );
}

function DataSection({ prefs, toggle }: any) {
  return (
    <div className="space-y-5 animate-fade-in">
      <Card padding="lg">
        <CardEyebrow>Data preferences</CardEyebrow>
        <CardTitle className="mt-1">How data is stored and used</CardTitle>
        <div className="mt-5 space-y-4">
          <Toggle
            label="Save analysis drafts automatically"
            description="Resume incomplete forms after a refresh."
            checked={prefs.autoSaveDrafts}
            onChange={() => toggle('autoSaveDrafts')}
          />
          <Toggle
            label="Keep analysis history"
            description="Retain previous analyses on this device."
            checked={prefs.persistHistory}
            onChange={() => toggle('persistHistory')}
          />
        </div>
      </Card>
    </div>
  );
}
