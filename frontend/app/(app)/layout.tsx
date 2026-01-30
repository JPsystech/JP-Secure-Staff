'use client'

import { usePathname } from 'next/navigation'
import { AnimatePresence, motion } from 'framer-motion'
import { AppShell } from '@/components/layout/AppShell'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { BreakpointIndicator } from '@/components/dev/BreakpointIndicator'

const pageTransition = {
  initial: { opacity: 0, y: 6 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: 4 },
  transition: { duration: 0.2, ease: 'easeOut' },
}

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  return (
    <ProtectedRoute>
      <AppShell>
        <BreakpointIndicator />
        <AnimatePresence mode="wait">
          <motion.div
            key={pathname}
            initial={pageTransition.initial}
            animate={pageTransition.animate}
            exit={pageTransition.exit}
            transition={pageTransition.transition}
            className="contents"
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </AppShell>
    </ProtectedRoute>
  )
}

