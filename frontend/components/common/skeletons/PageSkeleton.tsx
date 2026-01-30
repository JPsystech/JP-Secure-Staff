'use client'

import { Skeleton } from '@/components/ui/skeleton'
import { TableSkeleton } from './TableSkeleton'

export function PageSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <Skeleton className="h-8 w-48" />
          <Skeleton className="mt-2 h-4 w-72" />
        </div>
        <Skeleton className="h-9 w-32" />
      </div>
      <TableSkeleton rows={6} cols={5} />
    </div>
  )
}
