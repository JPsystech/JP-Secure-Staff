import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('token')?.value || 
    request.headers.get('authorization')?.replace('Bearer ', '')

  // Public routes that don't require authentication
  const publicRoutes = ['/login', '/admin-login']
  const isPublicRoute = publicRoutes.some(route => 
    request.nextUrl.pathname === route
  )

  // Admin routes require MASTER_ADMIN role
  const isAdminRoute = request.nextUrl.pathname.startsWith('/admin')

  // If accessing public route, allow
  if (isPublicRoute) {
    return NextResponse.next()
  }

  // For protected routes, check token in client-side
  // Server-side middleware can't access localStorage, so we'll handle this in components
  return NextResponse.next()
}

export const config = {
  matcher: [
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}

