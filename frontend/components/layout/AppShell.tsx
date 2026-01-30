'use client'

import { useState, useEffect } from 'react'
import { Menu } from 'lucide-react'
import { SidebarNav, SidebarNavContent, getAppNavGroups } from './SidebarNav'
import { Topbar } from './Topbar'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent } from '@/components/ui/sheet'
import { usePathname } from 'next/navigation'

interface AppShellProps {
  children: React.ReactNode
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname()
  const [user, setUser] = useState<any>(null)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      try {
        setUser(JSON.parse(userStr))
      } catch {
        setUser(null)
      }
    }
  }, [])

  const navGroups = getAppNavGroups(user)

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-background">
      <SidebarNav
        groups={navGroups}
        collapsed={sidebarCollapsed}
        onCollapsedChange={setSidebarCollapsed}
        showCollapseToggle={true}
      />
      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent side="left" className="w-64 p-0 flex flex-col [&>button]:hidden">
          <div className="flex h-14 items-center border-b border-border px-4">
            <span className="font-semibold text-foreground">JP Secure Staff</span>
          </div>
          <SidebarNavContent
            groups={navGroups}
            pathname={pathname}
            collapsed={false}
            showLabels={true}
            onNavigate={() => setMobileNavOpen(false)}
          />
        </SheetContent>
      </Sheet>
      <div className="flex flex-1 flex-col min-w-0 min-h-screen">
        <Topbar
          user={user}
          leftContent={
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden h-9 w-9 shrink-0"
              onClick={() => setMobileNavOpen(true)}
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </Button>
          }
        />
        <main className="flex-1 overflow-y-auto overflow-x-hidden min-h-0">
          <div className="content-container w-full min-w-0">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
