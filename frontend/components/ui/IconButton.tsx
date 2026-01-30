'use client'

import * as React from 'react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

export interface IconButtonProps extends React.ComponentProps<typeof Button> {
  /** Accessible label for screen readers */
  'aria-label': string
  /** Icon to show */
  icon: React.ReactNode
  /** Size: sm for table actions, default for primary */
  size?: 'default' | 'sm' | 'lg' | 'icon'
}

const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ className, icon, size = 'icon', children, ...props }, ref) => (
    <Button
      ref={ref}
      variant="ghost"
      size={size}
      className={cn(
        'h-8 w-8 p-0 text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors',
        size === 'sm' && 'h-7 w-7',
        className
      )}
      {...props}
    >
      {icon}
      {children}
    </Button>
  )
)
IconButton.displayName = 'IconButton'

export { IconButton }
