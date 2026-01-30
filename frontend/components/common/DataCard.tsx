'use client'

import { ReactNode } from 'react'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { cn } from '@/lib/utils'

export interface DataCardProps {
  /** Card title */
  title: string
  /** Optional description below title */
  description?: string
  /** Optional icon in header */
  icon?: ReactNode
  /** Optional actions in header (right) */
  actions?: ReactNode
  /** Card body */
  children: ReactNode
  className?: string
  /** Header class */
  headerClassName?: string
  /** No padding on content (e.g. for tables) */
  noPadding?: boolean
}

/**
 * Enterprise data card: header (title + optional icon/actions) + body.
 * Uses subtle shadow and border for consistency.
 */
export function DataCard({
  title,
  description,
  icon,
  actions,
  children,
  className,
  headerClassName,
  noPadding,
}: DataCardProps) {
  return (
    <Card className={cn('shadow-card border-border', className)}>
      <CardHeader className={cn('flex flex-row items-start justify-between gap-4 space-y-0 pb-4', headerClassName)}>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            {icon && <span className="text-muted-foreground">{icon}</span>}
            <h2 className="text-base font-medium tracking-tight text-foreground">{title}</h2>
          </div>
          {description && (
            <p className="text-sm text-muted-foreground">{description}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2">{actions}</div>}
      </CardHeader>
      <CardContent className={cn(noPadding && 'p-0')}>
        {children}
      </CardContent>
    </Card>
  )
}
