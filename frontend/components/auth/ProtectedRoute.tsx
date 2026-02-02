'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { auth } from '@/lib/api'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireAdmin?: boolean
}

export default function ProtectedRoute({ children, requireAdmin = false }: ProtectedRouteProps) {
  const router = useRouter()
  const pathname = usePathname()
  const [isLoading, setIsLoading] = useState(true)
  const [isAuthorized, setIsAuthorized] = useState(false)

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token')
      if (!token) {
        if (pathname !== '/login') router.push('/login')
        setIsLoading(false)
        return
      }
      try {
        const response = await auth.me()
        if (response.error) {
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          if (pathname !== '/login') router.push('/login')
          setIsLoading(false)
          return
        }
        if (response.data) {
          if (requireAdmin && response.data.role !== 'MASTER_ADMIN') {
            if (pathname !== '/dashboard') router.push('/dashboard')
            setIsLoading(false)
            return
          }
          setIsAuthorized(true)
        }
      } catch (error) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        if (pathname !== '/login') router.push('/login')
      } finally {
        setIsLoading(false)
      }
    }
    checkAuth()
  }, [pathname, requireAdmin])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!isAuthorized) {
    return null
  }

  return <>{children}</>
}

