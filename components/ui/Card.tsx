import { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'subtle' | 'outlined' | 'elevated';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const variantClasses = {
  default: 'bg-surface-card border border-border',
  subtle: 'bg-surface-muted border border-border-subtle',
  outlined: 'bg-transparent border border-border',
  elevated: 'bg-surface-card shadow-soft border border-border',
};

const paddingClasses = {
  none: '',
  sm: 'p-4',
  md: 'p-5',
  lg: 'p-6',
};

export function Card({ className, variant = 'default', padding = 'md', ...props }: CardProps) {
  return (
    <div
      className={cn('rounded-lg', variantClasses[variant], paddingClasses[padding], className)}
      {...props}
    />
  );
}

export function CardHeader({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('flex items-start justify-between mb-3 gap-3', className)}
      {...props}
    />
  );
}

export function CardTitle({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h3
      className={cn('text-base font-semibold text-ink leading-tight', className)}
      {...props}
    />
  );
}

export function CardDescription({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn('text-sm text-ink-secondary leading-relaxed', className)} {...props} />
  );
}

export function CardEyebrow({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'text-[11px] font-semibold tracking-wider uppercase text-primary',
        className
      )}
      {...props}
    />
  );
}
