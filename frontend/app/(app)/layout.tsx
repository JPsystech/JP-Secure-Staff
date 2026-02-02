'use client'

import { AppShell } from '@/components/layout/AppShell'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { BreakpointIndicator } from '@/components/dev/BreakpointIndicator'

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ProtectedRoute>
      <AppShell>
        <BreakpointIndicator />
        {children}
      </AppShell>
    </ProtectedRoute>
  )
}

