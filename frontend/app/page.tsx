'use client'

import { useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'

export default function Home() {
  const router = useRouter()
  const didRedirect = useRef(false)

  // Run once on mount only (this page only renders at /)
  useEffect(() => {
    if (didRedirect.current) return
    didRedirect.current = true
    if (process.env.NODE_ENV === 'development') {
      console.debug('[Home] redirect run once per mount')
    }
    const token = localStorage.getItem('token')
    if (token) {
      router.push('/dashboard')
    } else {
      router.push('/login')
    }
  }, [])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900"></div>
    </div>
  )
}

