import { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface ProgressBarProps extends HTMLAttributes<HTMLDivElement> {
  value: number; // 0–100
  size?: 'sm' | 'md' | 'lg';
  variant?: 'primary' | 'success' | 'warning' | 'danger' | 'muted';
  showValue?: boolean;
  indeterminate?: boolean;
}

const sizeClasses = {
  sm: 'h-1.5',
  md: 'h-2',
  lg: 'h-3',
};
const variantClasses = {
  primary: 'bg-primary',
  success: 'bg-success',
  warning: 'bg-warning',
  danger: 'bg-danger',
  muted: 'bg-ink-secondary',
};

export function ProgressBar({
  value,
  size = 'md',
  variant = 'primary',
  showValue,
  className,
  indeterminate,
  ...props
}: ProgressBarProps) {
  const safe = Math.max(0, Math.min(100, value));
  return (
    <div
      className={cn(
        'w-full bg-border-subtle rounded-full overflow-hidden',
        sizeClasses[size],
        className
      )}
      role="progressbar"
      aria-valuenow={safe}
      aria-valuemin={0}
      aria-valuemax={100}
      {...props}
    >
      {indeterminate ? (
        <div
          className={cn(
            'h-full w-1/3 animate-progress rounded-full',
            variantClasses[variant]
          )}
        />
      ) : (
        <div
          className={cn('h-full rounded-full transition-all duration-500', variantClasses[variant])}
          style={{ width: `${safe}%` }}
        />
      )}
    </div>
  );
}

interface StepIndicatorProps {
  steps: { id: string; label: string }[];
  current: number;
  completed?: number;
}

export function StepIndicator({ steps, current, completed = 0 }: StepIndicatorProps) {
  return (
    <ol className="flex items-start gap-0 w-full">
      {steps.map((step, i) => {
        const isCompleted = i < current || i < completed;
        const isActive = i === current;
        return (
          <li key={step.id} className="flex-1 flex flex-col items-stretch">
            <div className="flex items-center w-full">
              <div
                className={cn(
                  'shrink-0 h-7 w-7 rounded-full border-2 flex items-center justify-center text-[12px] font-semibold transition-all',
                  isCompleted && 'bg-primary border-primary text-white',
                  isActive && !isCompleted && 'border-primary text-primary bg-primary-50 ring-pulse',
                  !isActive && !isCompleted && 'border-border text-ink-secondary bg-white'
                )}
              >
                {isCompleted ? (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" className="h-3.5 w-3.5 pop-in">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                ) : (
                  i + 1
                )}
              </div>
              {i < steps.length - 1 && (
                <div className="flex-1 mx-2 -mt-0.5">
                  <div className="h-0.5 rounded-full bg-border overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-primary to-secondary transition-all duration-700 ease-out"
                      style={{ width: isCompleted ? '100%' : '0%' }}
                    />
                  </div>
                </div>
              )}
            </div>
            <span
              className={cn(
                'mt-2 text-[12px] leading-tight',
                isActive || isCompleted ? 'text-ink font-medium' : 'text-ink-secondary'
              )}
            >
              {step.label}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
