'use client'

import { useEffect, useState } from 'react'
import { usePathname } from 'next/navigation'
import { Menu } from 'lucide-react'
import { SidebarNav, SidebarNavContent, getAdminNavGroups } from '@/components/layout/SidebarNav'
import { AdminTopbar } from '@/components/layout/AdminTopbar'
import { Button } from '@/components/ui/button'
import { Sheet, SheetContent } from '@/components/ui/sheet'
import { auth } from '@/lib/api'

interface AdminShellProps {
  children: React.ReactNode
}

export default function AdminShell({ children }: AdminShellProps) {
  const pathname = usePathname()
  const [user, setUser] = useState<any>(null)
  const [permissionCodes, setPermissionCodes] = useState<string[]>([])
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
    auth.me().then((res) => {
      if (res.data && (res.data as { permission_codes?: string[] }).permission_codes) {
        setPermissionCodes((res.data as { permission_codes: string[] }).permission_codes)
      }
    })
  }, [])

  const navGroups = getAdminNavGroups(permissionCodes)

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-muted/30">
      <SidebarNav
        groups={navGroups}
        collapsed={sidebarCollapsed}
        onCollapsedChange={setSidebarCollapsed}
        showCollapseToggle={true}
      />
      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent side="left" className="w-64 p-0 flex flex-col [&>button]:hidden">
          <div className="flex h-14 items-center border-b border-border px-4">
            <span className="font-semibold text-foreground">Admin</span>
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
        <AdminTopbar
          user={user}
          title="Admin"
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
