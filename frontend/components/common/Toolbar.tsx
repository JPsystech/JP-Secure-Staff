'use client'

import { ReactNode } from 'react'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { Search } from 'lucide-react'

export interface ToolbarProps {
  /** Search input value */
  searchValue?: string
  /** Search placeholder */
  searchPlaceholder?: string
  /** Called when search input changes */
  onSearchChange?: (value: string) => void
  /** Left side: custom content (e.g. extra filters) */
  left?: ReactNode
  /** Right side: filter dropdowns + primary action */
  right?: ReactNode
  className?: string
}

/**
 * Enterprise toolbar: search (left), filters + primary action (right).
 * Responsive: wraps on small screens.
 */
export function Toolbar({
  searchValue = '',
  searchPlaceholder = 'Search...',
  onSearchChange,
  left,
  right,
  className,
}: ToolbarProps) {
  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-3',
        className
      )}
    >
      {(onSearchChange != null || searchPlaceholder) && (
        <div className="relative min-w-[200px] flex-1 sm:max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            type="search"
            placeholder={searchPlaceholder}
            value={searchValue}
            onChange={(e) => onSearchChange?.(e.target.value)}
            className="pl-9 h-9"
          />
        </div>
      )}
      {left && <div className="flex items-center gap-2">{left}</div>}
      {right && (
        <div className="ml-auto flex items-center gap-2">
          {right}
        </div>
      )}
    </div>
  )
}
