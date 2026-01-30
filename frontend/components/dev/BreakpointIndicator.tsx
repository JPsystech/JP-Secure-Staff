'use client'

import { useEffect, useState } from 'react'
import { cn } from '@/lib/utils'

const BREAKPOINTS = [
  { name: 'xs', max: 639 },
  { name: 'sm', max: 767 },
  { name: 'md', max: 1023 },
  { name: 'lg', max: 1279 },
  { name: 'xl', max: 1535 },
  { name: '2xl', max: Infinity },
]

function getBreakpoint(width: number) {
  for (const bp of BREAKPOINTS) {
    if (width <= bp.max) return bp.name
  }
  return '2xl'
}

/**
 * Dev-only: shows current breakpoint in bottom-right corner.
 * Renders nothing in production.
 */
export function BreakpointIndicator() {
  const [bp, setBp] = useState<string>('')
  const [width, setWidth] = useState(0)

  useEffect(() => {
    if (process.env.NODE_ENV === 'production') return
    const update = () => {
      const w = window.innerWidth
      setWidth(w)
      setBp(getBreakpoint(w))
    }
    update()
    window.addEventListener('resize', update)
    return () => window.removeEventListener('resize', update)
  }, [])

  if (process.env.NODE_ENV === 'production') return null

  return (
    <div
      className={cn(
        'fixed bottom-2 right-2 z-[9999] rounded-md border border-border bg-card px-2 py-1 text-[10px] font-mono text-muted-foreground shadow-md',
        'pointer-events-none select-none'
      )}
      aria-hidden
    >
      {bp} ({width}px)
    </div>
  )
}
