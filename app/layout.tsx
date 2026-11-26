import type { Metadata } from 'next';
import './globals.css';
import { AnalyzeProvider } from '@/components/AnalyzeContext';
import { AuthGate } from '@/components/AuthGate';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/ResearchFooter';

export const metadata: Metadata = {
  title: 'BiofilmAI — Rapid Detection of Biofilm-Forming Pathogens',
  description:
    'A multi-modal transformer framework integrating microscopy, spectroscopy, genomics, and clinical data with cross-attention fusion for rapid detection of biofilm-forming pathogens in chronic wound and implant infection.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">
        <AnalyzeProvider>
          <div className="flex min-h-screen flex-col">
            <Navbar />
            <main className="flex-1">
              <AuthGate>{children}</AuthGate>
            </main>
            <Footer />
          </div>
        </AnalyzeProvider>
      </body>
    </html>
  );
}
