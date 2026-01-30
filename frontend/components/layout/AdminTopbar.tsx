'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { User, LogOut, ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

interface AdminTopbarProps {
  user?: { full_name?: string; role_name?: string } | null
  title?: string
  breadcrumbs?: { label: string; href?: string }[]
  /** Left slot (e.g. hamburger on mobile) */
  leftContent?: React.ReactNode
  className?: string
}

export function AdminTopbar({ user, title, breadcrumbs, leftContent, className }: AdminTopbarProps) {
  const router = useRouter()

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/admin-login')
  }

  return (
    <header
      className={cn(
        'flex h-14 shrink-0 items-center justify-between border-b border-border bg-card px-3 sm:px-4 md:px-6 gap-2',
        className
      )}
    >
      <div className="flex min-w-0 flex-1 items-center gap-2 sm:gap-4">
        {leftContent}
        {breadcrumbs && breadcrumbs.length > 0 ? (
          <nav className="flex items-center gap-2 text-sm text-muted-foreground">
            {breadcrumbs.map((b, i) => (
              <span key={i} className="flex items-center gap-2">
                {i > 0 && <span aria-hidden>/</span>}
                {b.href ? (
                  <a href={b.href} className="hover:text-foreground transition-colors truncate">
                    {b.label}
                  </a>
                ) : (
                  <span className="truncate font-medium text-foreground">{b.label}</span>
                )}
              </span>
            ))}
          </nav>
        ) : title ? (
          <h1 className="truncate text-lg font-semibold text-foreground">{title}</h1>
        ) : (
          <span className="text-lg font-semibold text-foreground">JP Secure Staff — Admin</span>
        )}
      </div>

      <div className="flex items-center gap-2">
        {user && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2">
                <User className="h-4 w-4" />
                <span className="hidden max-w-[120px] truncate sm:inline">{user.full_name}</span>
                <ChevronDown className="h-4 w-4 shrink-0" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>
                <div className="flex flex-col gap-0.5">
                  <p className="text-sm font-medium">{user.full_name}</p>
                  <p className="text-xs text-muted-foreground">{user.role_name ?? 'Admin'}</p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout} className="cursor-pointer">
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </header>
  )
}
