'use client'

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Skeleton } from '@/components/ui/skeleton'
import { EmptyState } from '@/components/ui/EmptyState'
import { cn } from '@/lib/utils'

interface DataTableProps {
  /** Table header row (use TableHead inside TableRow) */
  header: React.ReactNode
  /** Table body rows */
  children: React.ReactNode
  /** Show loading skeleton instead of body */
  loading?: boolean
  /** When not loading and no rows, show this empty state */
  emptyTitle?: string
  emptyDescription?: string
  emptyAction?: React.ReactNode
  /** Number of skeleton rows when loading (default 6) */
  loadingRows?: number
  /** Whether there are zero data rows (for empty state) */
  isEmpty?: boolean
  /** Sticky header */
  stickyHeader?: boolean
  /** Very subtle zebra striping */
  zebra?: boolean
  className?: string
}

export function DataTable({
  header,
  children,
  loading,
  emptyTitle = 'No records found',
  emptyDescription = 'Try adjusting filters or add a new record.',
  emptyAction,
  loadingRows = 6,
  isEmpty,
  stickyHeader,
  zebra = true,
  className,
}: DataTableProps) {
  return (
    <div className={cn('rounded-2xl border border-border bg-card shadow-card-soft overflow-hidden', className)}>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className={cn(
              'hover:bg-transparent border-b bg-muted/60',
              stickyHeader && 'sticky top-0 z-10 bg-muted/95 backdrop-blur-sm'
            )}>
              {header}
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              Array.from({ length: loadingRows }).map((_, i) => (
                <TableRow key={i} className={cn('hover:bg-transparent border-b', zebra && i % 2 === 1 && 'bg-muted/20')}>
                  <TableCell colSpan={100} className="py-3">
                    <Skeleton className="h-8 w-full rounded" />
                  </TableCell>
                </TableRow>
              ))
            ) : isEmpty ? (
              <TableRow className="hover:bg-transparent">
                <TableCell colSpan={100} className="p-0">
                  <EmptyState
                    title={emptyTitle}
                    description={emptyDescription}
                    action={emptyAction}
                    className="border-0 bg-transparent py-10"
                  />
                </TableCell>
              </TableRow>
            ) : (
              children
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
