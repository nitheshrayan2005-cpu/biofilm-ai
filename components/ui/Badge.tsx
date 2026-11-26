import { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

type BadgeVariant = 'default' | 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'primary' | 'secondary';

const variantClasses: Record<BadgeVariant, string> = {
  default: 'bg-surface-muted text-ink-secondary border-border-subtle',
  success: 'bg-success-50 text-success-700 border-success-100',
  warning: 'bg-warning-50 text-warning-700 border-warning-100',
  danger: 'bg-danger-50 text-danger-700 border-danger-100',
  info: 'bg-primary-50 text-primary-700 border-primary-100',
  primary: 'bg-primary text-white border-primary',
  secondary: 'bg-secondary-50 text-secondary-700 border-secondary-100',
  neutral: 'bg-surface-muted text-ink border-border',
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
  dot?: boolean;
}

export function Badge({
  variant = 'default',
  size = 'md',
  dot,
  className,
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md border font-medium',
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-[12px]',
        variantClasses[variant],
        className
      )}
      {...props}
    >
      {dot && (
        <span
          className={cn(
            'inline-block w-1.5 h-1.5 rounded-full',
            variant === 'success' && 'bg-success',
            variant === 'warning' && 'bg-warning',
            variant === 'danger' && 'bg-danger',
            variant === 'primary' && 'bg-primary',
            variant === 'secondary' && 'bg-secondary',
            variant === 'info' && 'bg-primary',
            variant === 'neutral' && 'bg-ink-secondary',
            variant === 'default' && 'bg-ink-secondary'
          )}
        />
      )}
      {children}
    </span>
  );
}
