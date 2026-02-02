import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname

  if (process.env.NODE_ENV === 'development') {
    console.debug('[middleware] run once per request:', pathname)
  }

  // Safe guards: never redirect or modify _next, static assets, api, or files with extensions
  if (pathname.startsWith('/_next') || pathname.startsWith('/api') || pathname.includes('.')) {
    return NextResponse.next()
  }
  if (pathname === '/favicon.ico') {
    return NextResponse.next()
  }

  const token = request.cookies.get('token')?.value ||
    request.headers.get('authorization')?.replace('Bearer ', '')

  const publicRoutes = ['/login', '/admin-login']
  const isPublicRoute = publicRoutes.some((route) => pathname === route)

  if (isPublicRoute) {
    return NextResponse.next()
  }

  // Protected routes: auth is handled in ProtectedRoute (client); no redirect to same path
  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!api|_next/static|_next/image|favicon.ico).*)'],
}

