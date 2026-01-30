import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface StatPill {
  label: string
  value: string | number
  variant?: 'default' | 'secondary' | 'outline'
}

interface StatPillsProps {
  stats: StatPill[]
  className?: string
}

export function StatPills({ stats, className }: StatPillsProps) {
  return (
    <div className={cn("flex flex-wrap gap-3 mb-6", className)}>
      {stats.map((stat, index) => (
        <div key={index} className="flex items-center gap-2">
          <span className="text-sm text-gray-600">{stat.label}:</span>
          <Badge variant={stat.variant || 'secondary'} className="font-semibold">
            {stat.value}
          </Badge>
        </div>
      ))}
    </div>
  )
}

