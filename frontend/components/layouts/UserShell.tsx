'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Users, Wallet, FileText } from 'lucide-react'

interface UserShellProps {
  children: React.ReactNode
}

export default function UserShell({ children }: UserShellProps) {
  const router = useRouter()
  const pathname = usePathname()
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      setUser(JSON.parse(userStr))
    }
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    router.push('/login')
  }

  const isOperation = user?.role === 'OPS_USER'
  const isFinance = user?.role === 'FINANCE_USER'
  const isHR = user?.role === 'HR_USER'

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center space-x-8">
              <h1 className="text-xl font-semibold">JP Secure Staff</h1>
              <div className="flex space-x-4">
                {isOperation && (
                  <Link
                    href="/operation/create"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      pathname?.startsWith('/operation')
                        ? 'bg-primary text-primary-foreground'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    Create Person
                  </Link>
                )}
                {isFinance && (
                  <Link
                    href="/finance/inbox"
                    className={`px-3 py-2 rounded-md text-sm font-medium ${
                      pathname?.startsWith('/finance')
                        ? 'bg-primary text-primary-foreground'
                        : 'text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    Finance Inbox
                  </Link>
                )}
                {isHR && (
                  <>
                    <Link
                      href="/hr/intake"
                      className={`px-3 py-2 rounded-md text-sm font-medium ${
                        pathname?.startsWith('/hr/intake')
                          ? 'bg-primary text-primary-foreground'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      Create Person
                    </Link>
                    <Link
                      href="/hr/inbox"
                      className={`px-3 py-2 rounded-md text-sm font-medium ${
                        pathname?.startsWith('/hr/inbox')
                          ? 'bg-primary text-primary-foreground'
                          : 'text-gray-700 hover:bg-gray-100'
                      }`}
                    >
                      HR Inbox
                    </Link>
                  </>
                )}
                <Link
                  href="/cv-wallet"
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    pathname === '/cv-wallet'
                      ? 'bg-primary text-primary-foreground'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <Wallet className="w-4 h-4 inline mr-1" />
                  CV Wallet
                </Link>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {user && (
                <span className="text-sm text-gray-700">
                  {user.full_name} ({user.role_name || 'User'})
                </span>
              )}
              <Button variant="outline" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          </div>
        </div>
      </nav>
      <main>{children}</main>
    </div>
  )
}

