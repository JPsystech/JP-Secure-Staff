'use client'

import * as React from 'react'
import { cn } from '@/lib/utils'

export type ResponsiveTableVariant = 'scroll' | 'card-rows'

interface ResponsiveTableProps {
  /** Table content (thead + tbody or Table components) */
  children: React.ReactNode
  /** min-width for table when using scroll (default 900px) */
  minWidth?: number
  /** Optional wrapper class */
  className?: string
  /** scroll = horizontal scroll on small screens; card-rows = show card list on mobile, table on md+ */
  variant?: ResponsiveTableVariant
}

/**
 * Wraps a table so it doesn't break on mobile.
 * - scroll: single scrollable wrapper, table has min-width
 * - card-rows: use TableCardRows on mobile (render card list) and this wrapper shows table on md+
 */
export function ResponsiveTableScroll({
  children,
  minWidth = 900,
  className,
}: Omit<ResponsiveTableProps, 'variant'>) {
  return (
    <div className={cn('w-full overflow-x-auto -mx-3 sm:mx-0 px-3 sm:px-0', className)}>
      <div style={{ minWidth }} className="inline-block w-full align-top">
        {children}
      </div>
    </div>
  )
}

/**
 * Mobile card row for use with ResponsiveTableCardRows.
 */
export function TableCardRow({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div
      className={cn(
        'rounded-xl border border-border bg-card p-4 shadow-card transition-shadow hover:shadow-md w-full min-w-0',
        className
      )}
    >
      {children}
    </div>
  )
}

interface ResponsiveTableCardRowsProps {
  /** Table (desktop): shown on md+ */
  table: React.ReactNode
  /** Card list (mobile): shown below md */
  cardList: React.ReactNode
  className?: string
}

/**
 * Renders card list on mobile, table on md+.
 */
export function ResponsiveTableCardRows({ table, cardList, className }: ResponsiveTableCardRowsProps) {
  return (
    <div className={cn('w-full min-w-0', className)}>
      <div className="md:hidden space-y-3">{cardList}</div>
      <div className="hidden md:block w-full overflow-x-auto">
        {table}
      </div>
    </div>
  )
}
