'use client'

import * as React from 'react'
import { Search } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Input } from '@/components/ui/input'

export interface SearchInputProps extends Omit<React.ComponentProps<typeof Input>, 'type'> {
  /** Optional icon (default: Search) */
  icon?: React.ReactNode
}

const SearchInput = React.forwardRef<HTMLInputElement, SearchInputProps>(
  ({ className, icon, ...props }, ref) => (
    <div className="relative">
      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
        {icon ?? <Search className="h-4 w-4" />}
      </span>
      <Input
        ref={ref}
        type="search"
        className={cn(
          'h-10 pl-9 pr-4 focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
          className
        )}
        {...props}
      />
    </div>
  )
)
SearchInput.displayName = 'SearchInput'

export { SearchInput }
