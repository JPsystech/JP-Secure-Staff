import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

export function getStatusBadgeVariant(status: string): "default" | "secondary" | "outline" {
  switch (status) {
    case 'ACTIVE':
      return 'default' // green
    case 'SENT_TO_HR':
      return 'secondary' // amber
    case 'SUBMITTED_TO_FINANCE':
      return 'outline' // blue
    case 'DRAFT':
      return 'outline' // gray
    default:
      return 'outline'
  }
}

export function getStatusColorClass(status: string): string {
  switch (status) {
    case 'ACTIVE':
      return 'bg-green-100 text-green-800 border-green-200'
    case 'SENT_TO_HR':
      return 'bg-amber-100 text-amber-800 border-amber-200'
    case 'SUBMITTED_TO_FINANCE':
      return 'bg-blue-100 text-blue-800 border-blue-200'
    case 'DRAFT':
      return 'bg-gray-100 text-gray-800 border-gray-200'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

export function formatStatus(status: string): string {
  return status.replace(/_/g, ' ')
}

interface StatusBadgeProps {
  status: string
  className?: string
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <Badge 
      variant={getStatusBadgeVariant(status)} 
      className={cn(getStatusColorClass(status), className)}
    >
      {formatStatus(status)}
    </Badge>
  )
}

