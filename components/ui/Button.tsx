import { ButtonHTMLAttributes, forwardRef } from 'react';
import { cn } from '@/lib/utils';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'outline' | 'subtle' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  iconLeft?: React.ReactNode;
  iconRight?: React.ReactNode;
  fullWidth?: boolean;
}

const variantClasses = {
  primary:
    'bg-primary text-white hover:bg-primary-700 active:bg-primary-800 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed',
  secondary:
    'bg-secondary text-white hover:bg-secondary-700 active:bg-secondary-800 shadow-sm disabled:opacity-50',
  outline:
    'border border-border bg-white text-ink hover:bg-primary-50 hover:border-primary-300 hover:text-primary-700',
  ghost:
    'bg-transparent text-ink hover:bg-primary-50 hover:text-primary-700 disabled:opacity-50',
  subtle:
    'bg-primary-50 text-primary-700 hover:bg-primary-100 active:bg-primary-200 disabled:opacity-50',
  danger:
    'bg-danger text-white hover:bg-danger-700 shadow-sm disabled:opacity-50',
};

const sizeClasses = {
  sm: 'h-9 px-3 text-sm font-medium rounded-md',
  md: 'h-10 px-4 text-sm font-medium rounded-md',
  lg: 'h-11 px-5 text-[15px] font-medium rounded-md',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      loading,
      iconLeft,
      iconRight,
      fullWidth,
      children,
      disabled,
      ...rest
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        className={cn(
          'inline-flex items-center justify-center gap-2 transition-colors transition-shadow duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-300 focus-visible:ring-offset-2 focus-visible:ring-offset-surface-background whitespace-nowrap',
          variantClasses[variant],
          sizeClasses[size],
          fullWidth && 'w-full',
          className
        )}
        disabled={disabled || loading}
        {...rest}
      >
        {loading ? (
          <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.25" />
            <path
              d="M4 12a8 8 0 018-8"
              stroke="currentColor"
              strokeWidth="3"
              strokeLinecap="round"
            />
          </svg>
        ) : iconLeft}
        {children}
        {iconRight}
      </button>
    );
  }
);

Button.displayName = 'Button';
