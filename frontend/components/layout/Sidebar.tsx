'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  UserPlus,
  Wallet,
  FileText,
  Users,
  Ticket,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

interface SidebarProps {
  user?: any
}

export function Sidebar({ user }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false)
  const pathname = usePathname()

  const isOperation = user?.role === 'OPS_USER'
  const isFinance = user?.role === 'FINANCE_USER'
  const isHR = user?.role === 'HR_USER'
  const isAdmin = user?.role === 'MASTER_ADMIN'

  const menuItems = [
    {
      label: 'Dashboard',
      href: '/dashboard',
      icon: LayoutDashboard,
      show: true,
    },
    // Operations-specific menu
    ...(isOperation || isAdmin ? [
      {
        label: 'Create Person',
        href: '/persons/new',
        icon: UserPlus,
        show: true,
      },
      {
        label: 'My Submissions',
        href: '/persons',
        icon: FileText,
        show: true,
      },
    ] : []),
    {
      label: 'CV Wallet',
      href: '/cv-wallet',
      icon: Wallet,
      show: true,
    },
    // Finance-specific menu
    {
      label: 'Finance Inbox',
      href: '/tickets',
      icon: FileText,
      show: isFinance || isAdmin,
    },
    // HR-specific menu
    ...(isHR || isAdmin ? [
      {
        label: 'HR Create Person',
        href: '/persons/new',
        icon: UserPlus,
        show: !isOperation, // if user is both OPS and HR, use OPS menu above
      },
      {
        label: 'HR Inbox',
        href: '/tickets',
        icon: Users,
        show: !isOperation,
      },
    ] : []),
    {
      label: 'My Tickets',
      href: '/tickets',
      icon: Ticket,
      show: true,
    },
    ...(isFinance || isHR || isAdmin ? [
      {
        label: 'Dept Inbox',
        href: '/tickets/inbox',
        icon: FileText,
        show: true,
      },
    ] : []),
  ].filter(item => item.show)

  return (
    <div
      className={cn(
        "bg-white border-r border-gray-200 transition-all duration-300 flex flex-col",
        collapsed ? "w-16" : "w-64"
      )}
    >
      <div className="flex items-center justify-between p-4 border-b">
        {!collapsed && (
          <h2 className="text-lg font-semibold text-gray-900">JP Secure Staff</h2>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(!collapsed)}
          className="ml-auto"
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {menuItems.map((item) => {
          const Icon = item.icon
          const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')
          
          return (
            <Link
              key={item.href}
              href={item.href}
              prefetch={false}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-indigo-50 text-indigo-700"
                  : "text-gray-700 hover:bg-gray-100"
              )}
            >
              <Icon className={cn("h-5 w-5 flex-shrink-0", isActive && "text-indigo-600")} />
              {!collapsed && <span>{item.label}</span>}
            </Link>
          )
        })}
      </nav>
    </div>
  )
}

