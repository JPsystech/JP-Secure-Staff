'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
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
  Building2,
  Shield,
  Database,
  Settings,
  FileSearch,
  UserCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'

export interface NavItem {
  label: string
  href: string
  icon: React.ComponentType<{ className?: string }>
}

export interface NavGroup {
  label?: string
  items: NavItem[]
}

interface SidebarNavProps {
  groups: NavGroup[]
  collapsed?: boolean
  onCollapsedChange?: (collapsed: boolean) => void
  showCollapseToggle?: boolean
}

/** Shared nav list content for desktop sidebar and mobile sheet */
export function SidebarNavContent({
  groups,
  pathname,
  collapsed = false,
  showLabels = true,
  onNavigate,
}: {
  groups: NavGroup[]
  pathname: string
  collapsed?: boolean
  showLabels?: boolean
  onNavigate?: () => void
}) {
  return (
    <nav className="flex-1 space-y-6 overflow-y-auto p-3">
      {groups.map((group, gIdx) => (
        <div key={gIdx} className="space-y-1">
          {group.label && showLabels && !collapsed && (
            <p className="px-3 py-1.5 text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
              {group.label}
            </p>
          )}
          <ul className="space-y-0.5">
            {group.items.map((item) => {
              const Icon = item.icon
              const isActive =
                pathname === item.href || (item.href !== '/' && pathname?.startsWith(item.href))
              const uniqueKey = `${group.label ?? 'nav'}-${item.label}-${item.href}`
              return (
                <li key={uniqueKey}>
                  <Link
                    href={item.href}
                    prefetch={false}
                    onClick={onNavigate}
                    className={cn(
                      'relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors duration-150',
                      isActive
                        ? 'bg-primary/10 text-primary [&_.nav-icon]:text-primary'
                        : 'text-muted-foreground hover:bg-muted/80 hover:text-foreground'
                    )}
                  >
                    {isActive && (
                      <motion.span
                        layoutId="sidebar-active"
                        className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r-full bg-primary"
                        transition={{ type: 'tween', duration: 0.2 }}
                      />
                    )}
                    <Icon className={cn('h-5 w-5 shrink-0 nav-icon', isActive && 'text-primary')} />
                    {!collapsed && <span className="truncate">{item.label}</span>}
                  </Link>
                </li>
              )
            })}
          </ul>
        </div>
      ))}
    </nav>
  )
}

export function SidebarNav({
  groups,
  collapsed = false,
  onCollapsedChange,
  showCollapseToggle = true,
}: SidebarNavProps) {
  const pathname = usePathname()

  return (
    <aside
      className={cn(
        'hidden md:flex md:flex-col border-r border-border bg-card shadow-card transition-all duration-200 shrink-0',
        collapsed ? 'md:w-[4.5rem]' : 'md:w-64'
      )}
    >
      <div className="flex h-14 items-center justify-between border-b border-border px-3 gap-1 w-full">
        {!collapsed && (
          <span className="truncate text-base font-semibold text-foreground">JP Secure Staff</span>
        )}
        {showCollapseToggle && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors"
            onClick={() => onCollapsedChange?.(!collapsed)}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        )}
      </div>
      <SidebarNavContent groups={groups} pathname={pathname} collapsed={collapsed} showLabels={true} />
    </aside>
  )
}

/** Build app (user) nav groups from user role */
export function getAppNavGroups(user?: { role?: string } | null): NavGroup[] {
  const isOperation = user?.role === 'OPS_USER'
  const isFinance = user?.role === 'FINANCE_USER'
  const isHR = user?.role === 'HR_USER'
  const isAdmin = user?.role === 'MASTER_ADMIN'

  const groups: NavGroup[] = [
    {
      items: [
        { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
      ],
    },
    ...(isOperation || isAdmin
      ? [
          {
            label: 'Operations',
            items: [
              { label: 'Create Person', href: '/operation/create', icon: UserPlus },
              { label: 'My Submissions', href: '/persons', icon: FileText },
            ],
          },
        ]
      : []),
    {
      items: [{ label: 'CV Wallet', href: '/cv-wallet', icon: Wallet }],
    },
    ...(isFinance || isAdmin
      ? [
          {
            label: 'Finance',
            items: [{ label: 'Finance Inbox', href: '/tickets', icon: FileText }],
          },
        ]
      : []),
    ...(isHR || isAdmin
      ? [
          {
            label: 'HR',
            items: [
              { label: 'HR Create Person', href: '/operation/create', icon: UserPlus },
              { label: 'HR Inbox', href: '/tickets', icon: Users },
            ],
          },
        ]
      : []),
    {
      label: 'Tickets',
      items: [
        { label: 'My Tickets', href: '/tickets', icon: Ticket },
        ...(isFinance || isHR || isAdmin
          ? [{ label: 'Dept Inbox', href: '/tickets/inbox', icon: FileText }]
          : []),
      ].filter(Boolean) as NavItem[],
    },
  ]
  return groups
}

/** Admin nav: Persons (if permission) + Departments, Roles, Users, etc. */
export function getAdminNavGroups(permissionCodes: string[]): NavGroup[] {
  const hasPersonView = permissionCodes.includes('ADMIN_PERSON_VIEW_ALL')
  const groups: NavGroup[] = []
  if (hasPersonView) {
    groups.push({
      items: [{ label: 'Persons', href: '/admin/persons', icon: UserCircle }],
    })
  }
  groups.push({
    label: 'Admin',
    items: [
      { label: 'Departments', href: '/admin/departments', icon: Building2 },
      { label: 'Roles & Permissions', href: '/admin/roles-permissions', icon: Shield },
      { label: 'Users', href: '/admin/users', icon: Users },
      { label: 'Master Data', href: '/admin/master-data', icon: Database },
      { label: 'Policies', href: '/admin/policies', icon: Settings },
      { label: 'Templates', href: '/admin/templates', icon: FileText },
      { label: 'Audit Logs', href: '/admin/audit', icon: FileSearch },
    ],
  })
  return groups
}
