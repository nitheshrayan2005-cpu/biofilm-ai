import { cn } from '@/lib/utils';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
  withWordmark?: boolean;
  withSubtitle?: boolean;
  className?: string;
}

export function Logo({ size = 'md', withWordmark = true, withSubtitle = false, className }: LogoProps) {
  const sizeClasses = {
    sm: { icon: 'h-7 w-7', text: 'text-base', sub: 'text-[10px]' },
    md: { icon: 'h-9 w-9', text: 'text-lg', sub: 'text-[11px]' },
    lg: { icon: 'h-11 w-11', text: 'text-xl', sub: 'text-xs' },
  };
  const s = sizeClasses[size];

  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <LogoMark size={size} />
      {withWordmark && (
        <div className="flex flex-col leading-none">
          <span className={cn('font-semibold tracking-tight text-ink', s.text)}>
            Biofilm<span className="text-primary">AI</span>
          </span>
          {withSubtitle && (
            <span className={cn('text-ink-secondary uppercase tracking-wider mt-0.5', s.sub)}>
              Biofilm Pathogen Detection
            </span>
          )}
        </div>
      )}
    </div>
  );
}

interface LogoMarkProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export function LogoMark({ size = 'md', className }: LogoMarkProps) {
  const dim = { sm: 28, md: 36, lg: 44 };
  const d = dim[size];
  return (
    <div
      aria-hidden
      className={cn(
        'relative shrink-0 rounded-md bg-gradient-to-br from-primary to-secondary flex items-center justify-center shadow-sm',
        className
      )}
      style={{ width: d, height: d }}
    >
      <svg viewBox="0 0 24 24" fill="none" className={cn('text-white', size === 'sm' ? 'h-4 w-4' : size === 'md' ? 'h-5 w-5' : 'h-6 w-6')}>
        {/* Stylized microbial cell with cross/network */}
        <circle cx="12" cy="12" r="3.2" fill="currentColor" />
        <circle cx="12" cy="12" r="6" stroke="currentColor" strokeOpacity="0.6" strokeWidth="1.2" />
        <path
          d="M12 5.2v2 M12 16.8v2 M5.2 12h2 M16.8 12h2 M7 7l1.4 1.4 M15.6 15.6L17 17 M7 17l1.4-1.4 M15.6 8.4L17 7"
          stroke="currentColor"
          strokeOpacity="0.7"
          strokeWidth="1.2"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
}
