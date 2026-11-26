'use client';

import { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface StatusBannerProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'info' | 'success' | 'warning' | 'danger' | 'neutral';
  icon?: React.ReactNode;
  title?: string;
  description?: React.ReactNode;
}

const variantStyles = {
  info: 'bg-primary-50 border-primary-100 text-primary-800',
  success: 'bg-success-50 border-success-100 text-success-700',
  warning: 'bg-warning-50 border-warning-100 text-warning-700',
  danger: 'bg-danger-50 border-danger-100 text-danger-700',
  neutral: 'bg-surface-muted border-border text-ink',
};

export function StatusBanner({
  variant = 'info',
  icon,
  title,
  description,
  className,
  children,
  ...props
}: StatusBannerProps) {
  return (
    <div
      role={variant === 'danger' || variant === 'warning' ? 'alert' : undefined}
      className={cn(
        'rounded-md border px-4 py-3 flex gap-3',
        variantStyles[variant],
        className
      )}
      {...props}
    >
      {icon && <div className="shrink-0 mt-0.5">{icon}</div>}
      <div className="flex-1 text-sm">
        {title && <p className="font-medium mb-0.5">{title}</p>}
        {description && <div className="text-[13px] opacity-90">{description}</div>}
        {children}
      </div>
    </div>
  );
}

export function Divider({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('h-px bg-border-subtle my-4', className)} {...props} />;
}

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-12 px-6">
      {icon && (
        <div className="h-14 w-14 rounded-full bg-primary-50 text-primary flex items-center justify-center mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-base font-semibold text-ink mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-ink-secondary max-w-sm mb-4">{description}</p>
      )}
      {action}
    </div>
  );
}
