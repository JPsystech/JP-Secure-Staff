'use client'

import { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

export interface PageShellProps {
  /** Page title (h1) */
  title: string
  /** Optional subtitle below title */
  subtitle?: string
  /** Optional breadcrumb or extra info above title */
  breadcrumb?: ReactNode
  /** Right-side actions (buttons, etc.) */
  actions?: ReactNode
  /** Main content */
  children: ReactNode
  /** Outer wrapper class */
  className?: string
  /** Disable page entrance animation */
  noAnimation?: boolean
}

const pageVariants = {
  initial: { opacity: 0, y: 6 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 4 },
}

/**
 * Enterprise page shell: header (title, subtitle, actions) + content with subtle entrance animation.
 */
export function PageShell({
  title,
  subtitle,
  breadcrumb,
  actions,
  children,
  className,
  noAnimation,
}: PageShellProps) {
  const content = (
    <div className={cn('space-y-6 w-full min-w-0', className)}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
        <div className="min-w-0">
          {breadcrumb && (
            <div className="mb-1 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {breadcrumb}
            </div>
          )}
          <h1 className="text-xl sm:text-2xl font-semibold tracking-tight text-foreground truncate">{title}</h1>
          {subtitle && (
            <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
          )}
        </div>
        {actions && (
          <div className="flex flex-shrink-0 flex-wrap items-center gap-2 w-full sm:w-auto">{actions}</div>
        )}
      </div>
      {noAnimation ? children : (
        <motion.div
          initial="initial"
          animate="animate"
          variants={pageVariants}
          transition={{ duration: 0.2, ease: 'easeOut' }}
        >
          {children}
        </motion.div>
      )}
    </div>
  )
  return content
}
