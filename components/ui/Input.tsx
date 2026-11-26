import { InputHTMLAttributes, SelectHTMLAttributes, TextareaHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, hint, error, id, ...props }, ref) => {
    const inputId = id || props.name;
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-[13px] font-medium text-ink">
            {label}
            {props.required && <span className="text-danger ml-0.5">*</span>}
          </label>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            'h-10 px-3 text-sm rounded-md border bg-white text-ink placeholder:text-ink-secondary/60',
            'focus:border-primary focus:ring-2 focus:ring-primary-100 focus:outline-none',
            'transition-colors duration-150',
            error ? 'border-danger focus:border-danger focus:ring-danger-100' : 'border-border',
            className
          )}
          {...props}
        />
        {hint && !error && <p className="text-xs text-ink-secondary">{hint}</p>}
        {error && <p className="text-xs text-danger">{error}</p>}
      </div>
    );
  }
);

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string;
  hint?: string;
  error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, label, hint, error, id, ...props }, ref) => {
    const inputId = id || props.name;
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-[13px] font-medium text-ink">
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={inputId}
          className={cn(
            'min-h-[88px] px-3 py-2 text-sm rounded-md border bg-white text-ink placeholder:text-ink-secondary/60',
            'focus:border-primary focus:ring-2 focus:ring-primary-100 focus:outline-none',
            'transition-colors duration-150 resize-y',
            error ? 'border-danger focus:border-danger focus:ring-danger-100' : 'border-border',
            className
          )}
          {...props}
        />
        {hint && !error && <p className="text-xs text-ink-secondary">{hint}</p>}
        {error && <p className="text-xs text-danger">{error}</p>}
      </div>
    );
  }
);

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  hint?: string;
  error?: string;
  options: { value: string; label: string }[];
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, hint, error, id, options, ...props }, ref) => {
    const inputId = id || props.name;
    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-[13px] font-medium text-ink">
            {label}
            {props.required && <span className="text-danger ml-0.5">*</span>}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={inputId}
            className={cn(
              'h-10 w-full px-3 pr-9 text-sm rounded-md border bg-white text-ink appearance-none',
              'focus:border-primary focus:ring-2 focus:ring-primary-100 focus:outline-none',
              'transition-colors duration-150',
              error ? 'border-danger focus:border-danger focus:ring-danger-100' : 'border-border',
              className
            )}
            {...props}
          >
            {options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <svg
            className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-ink-secondary"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <polyline points="6 9 12 15 18 9" />
          </svg>
        </div>
        {hint && !error && <p className="text-xs text-ink-secondary">{hint}</p>}
        {error && <p className="text-xs text-danger">{error}</p>}
      </div>
    );
  }
);

interface ToggleProps {
  label?: string;
  description?: string;
  checked: boolean;
  onChange: (v: boolean) => void;
  id?: string;
}

export function Toggle({ label, description, checked, onChange, id }: ToggleProps) {
  const tId = id || 'toggle-' + Math.random().toString(36).slice(2, 8);
  return (
    <div className="flex items-center justify-between gap-3">
      <div className="flex flex-col">
        {label && (
          <label htmlFor={tId} className="text-[13px] font-medium text-ink cursor-pointer">
            {label}
          </label>
        )}
        {description && <p className="text-xs text-ink-secondary">{description}</p>}
      </div>
      <button
        id={tId}
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-150',
          checked ? 'bg-primary' : 'bg-border'
        )}
      >
        <span
          className={cn(
            'pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow transition duration-150',
            checked ? 'translate-x-4' : 'translate-x-0'
          )}
        />
      </button>
    </div>
  );
}
