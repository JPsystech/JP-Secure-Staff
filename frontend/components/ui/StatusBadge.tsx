'use client'

import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

/** Statuses used across the app: person, ticket, document, etc. */
const STATUS_CONFIG: Record<string, { variant: 'default' | 'secondary' | 'outline' | 'destructive'; className: string; label: string }> = {
  // Person / profile
  DRAFT: { variant: 'outline', className: 'bg-muted text-muted-foreground border-muted-foreground/30', label: 'Draft' },
  SUBMITTED_TO_FINANCE: { variant: 'outline', className: 'bg-blue-50 text-blue-800 border-blue-200', label: 'Submitted to Finance' },
  FINANCE_IN_PROGRESS: { variant: 'secondary', className: 'bg-sky-50 text-sky-800 border-sky-200', label: 'Finance In Progress' },
  SENT_TO_HR: { variant: 'secondary', className: 'bg-amber-50 text-amber-800 border-amber-200', label: 'Sent to HR' },
  ACTIVE: { variant: 'default', className: 'bg-green-50 text-green-800 border-green-200', label: 'Active' },
  HR_COMPLETED: { variant: 'default', className: 'bg-emerald-50 text-emerald-800 border-emerald-200', label: 'HR Completed' },
  // Ticket / grant
  OPEN: { variant: 'outline', className: 'bg-muted text-muted-foreground', label: 'Open' },
  IN_PROGRESS: { variant: 'secondary', className: 'bg-blue-50 text-blue-800 border-blue-200', label: 'In Progress' },
  WAITING: { variant: 'secondary', className: 'bg-amber-50 text-amber-800', label: 'Waiting' },
  RESOLVED: { variant: 'default', className: 'bg-green-50 text-green-800 border-green-200', label: 'Resolved' },
  CLOSED: { variant: 'outline', className: 'bg-muted text-muted-foreground', label: 'Closed' },
  PENDING: { variant: 'secondary', className: 'bg-amber-50 text-amber-800', label: 'Pending' },
  APPROVED: { variant: 'default', className: 'bg-green-50 text-green-800', label: 'Approved' },
  REJECTED: { variant: 'destructive', className: 'bg-red-50 text-red-800 border-red-200', label: 'Rejected' },
  EXPIRED: { variant: 'outline', className: 'bg-muted text-muted-foreground line-through', label: 'Expired' },
  // Priority (for display)
  LOW: { variant: 'outline', className: 'bg-gray-50 text-gray-700', label: 'Low' },
  NORMAL: { variant: 'secondary', className: 'bg-blue-50 text-blue-800', label: 'Normal' },
  HIGH: { variant: 'destructive', className: 'bg-red-50 text-red-800 border-red-200', label: 'High' },
  // Document / generic
  available: { variant: 'default', className: 'bg-green-50 text-green-800', label: 'Available' },
  unavailable: { variant: 'outline', className: 'bg-muted text-muted-foreground', label: 'Unavailable' },
}

function getConfig(status: string) {
  const key = (status || '').toUpperCase().replace(/-/g, '_')
  return STATUS_CONFIG[key] ?? {
    variant: 'outline' as const,
    className: 'bg-muted text-muted-foreground',
    label: status ? status.replace(/_/g, ' ') : '—',
  }
}

interface StatusBadgeProps {
  status: string
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = getConfig(status)
  return (
    <Badge
      variant={config.variant}
      className={cn('font-medium', config.className, className)}
    >
      {config.label}
    </Badge>
  )
}

/** For use with existing getStatusBadgeVariant / getStatusColorClass / formatStatus */
export { getStatusBadgeVariant, getStatusColorClass, formatStatus } from '@/lib/status-badge'
