'use client';

import { useRef, useState, DragEvent } from 'react';
import { Upload, X, FileText, Image as ImageIcon, FileSpreadsheet, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { cn, formatFileSize } from '@/lib/utils';
import { Badge } from '@/components/ui/Badge';

export interface UploadableFile {
  file: File;
  preview?: string | null;
}

interface FileUploadProps {
  accept: string;
  examples: string[];
  maxSizeMB?: number;
  file: File | null;
  onFile: (f: File | null, preview?: string | null) => void;
  hint?: string;
  icon?: 'image' | 'chart' | 'dna' | 'generic';
  title?: string;
  description?: string;
}

const iconMap = {
  image: ImageIcon,
  chart: FileSpreadsheet,
  dna: FileText,
  generic: FileText,
};

export function FileUpload({
  accept,
  examples,
  maxSizeMB = 50,
  file,
  onFile,
  hint,
  icon = 'generic',
  title,
  description,
}: FileUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const Icon = iconMap[icon];

  function validate(f: File): string | null {
    const exts = accept.split(',').map((e) => e.trim().toLowerCase());
    const dot = '.' + (f.name.split('.').pop()?.toLowerCase() || '');
    const mimeOk = f.type && accept.includes(f.type.split('/')[0]) ? true : null;
    const ok = exts.some((e) => (e.startsWith('.') ? e === dot : e.includes('/') ? f.type.startsWith(e.replace('/*', '')) : false));
    if (!ok && !mimeOk) {
      return `Unable to process this file. Please upload a supported ${examples.join(', ')} file.`;
    }
    if (f.size > maxSizeMB * 1024 * 1024) {
      return `File is too large. Maximum size is ${maxSizeMB}MB.`;
    }
    return null;
  }

  function read(f: File) {
    const err = validate(f);
    if (err) {
      setError(err);
      return;
    }
    setError(null);

    // Build preview when possible (images only)
    if (f.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (ev) => onFile(f, ev.target?.result as string);
      reader.readAsDataURL(f);
    } else {
      const reader = new FileReader();
      reader.onload = () => onFile(f, null);
      reader.readAsText(f.slice(0, 1024 * 200));
    }
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragActive(false);
    const f = e.dataTransfer.files?.[0];
    if (f) read(f);
  }

  function remove() {
    setError(null);
    onFile(null, null);
    if (inputRef.current) inputRef.current.value = '';
  }

  return (
    <div>
      {title && (
        <div className="mb-3">
          <p className="text-sm font-semibold text-ink">{title}</p>
          {description && <p className="text-xs text-ink-secondary mt-0.5">{description}</p>}
        </div>
      )}

      <div
        onDragEnter={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragActive(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setDragActive(false);
        }}
        onDrop={onDrop}
        className={cn(
          'rounded-lg border border-dashed bg-surface-muted transition-all duration-300',
          dragActive && 'border-primary bg-primary-50 scale-[1.01] shadow-[0_0_0_4px_rgba(23,107,135,0.12)]',
          !dragActive && !file && 'border-border-strong',
          file && 'border-border bg-white'
        )}
      >
        {file ? (
          <div className="pop-in">
            <FilePreview
              file={file}
              onRemove={remove}
              onReplace={() => inputRef.current?.click()}
              previewOnly={icon === 'image'}
            />
          </div>
        ) : (
          <div className="px-6 py-10 flex flex-col items-center text-center">
            <div className={cn(
              'h-12 w-12 rounded-lg bg-primary-50 text-primary flex items-center justify-center mb-3 transition-transform duration-300',
              dragActive ? '-translate-y-1 scale-110' : 'animate-pulse-soft'
            )}>
              <Upload className="h-5 w-5" />
            </div>
            <p className="text-sm font-medium text-ink">Drop {title?.toLowerCase() || 'file'} here</p>
            <p className="text-xs text-ink-secondary mt-1">or browse to upload</p>
            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              className="mt-4 inline-flex items-center gap-1.5 text-[13px] font-medium text-primary hover:text-primary-700"
            >
              Browse files →
            </button>
            <p className="mt-4 text-[11px] text-ink-secondary">Supports: {examples.join(', ')}</p>
          </div>
        )}

        <input
          ref={inputRef}
          type="file"
          accept={accept}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) read(f);
          }}
          className="hidden"
          aria-label="Upload file"
        />
      </div>

      {hint && !error && <p className="mt-2 text-[11px] text-ink-secondary">{hint}</p>}
      {error && (
        <div className="mt-2 flex items-start gap-2 text-[12px] text-danger">
          <AlertCircle className="h-3.5 w-3.5 mt-0.5 shrink-0" />
          <span>{error}</span>
        </div>
      )}
    </div>
  );
}

function FilePreview({
  file,
  onRemove,
  onReplace,
  previewOnly,
}: {
  file: File;
  onRemove: () => void;
  onReplace: () => void;
  previewOnly?: boolean;
}) {
  return (
    <div className="p-5">
      {previewOnly && file.type.startsWith('image/') && (
        <div className="mb-4 flex items-center justify-center bg-surface-muted/50 rounded-md p-3">
          <div className="relative overflow-hidden rounded">
            <img
              src={URL.createObjectURL(file)}
              alt="Uploaded preview"
              className="max-h-56 rounded object-contain"
            />
            <div className="scan-line scan-once" />
          </div>
        </div>
      )}

      {!previewOnly && (
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-md bg-primary-50 text-primary flex items-center justify-center shrink-0">
            <FileText className="h-5 w-5" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-ink truncate">{file.name}</p>
            <p className="text-xs text-ink-secondary">
              {formatFileSize(file.size)} · {file.type || file.name.split('.').pop()?.toUpperCase()}
            </p>
          </div>
        </div>
      )}

      <div className={cn('flex flex-wrap items-center gap-2', previewOnly && 'justify-between')}>
        <Badge variant="success" size="sm" dot>
          File ready for analysis
        </Badge>
        <div className="flex items-center gap-2 ml-auto">
          <Button size="sm" variant="outline" onClick={onReplace}>
            Replace
          </Button>
          <Button size="sm" variant="ghost" onClick={onRemove} iconLeft={<X className="h-4 w-4" />}>
            Remove
          </Button>
        </div>
      </div>
    </div>
  );
}
