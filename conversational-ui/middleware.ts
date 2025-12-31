import { type NextRequest, NextResponse } from 'next/server';
import NextAuth from 'next-auth';
import { authConfig } from '@/app/(auth)/auth.config';

const { auth } = NextAuth(authConfig);

export default function middleware(req: NextRequest) {
  const url = req.nextUrl;
  const pending = req.cookies.get('pending_checkout');
  const billingStatus = url.searchParams.get('billing');

  // Clear pending checkout after returning from Stripe
  if (billingStatus === 'success' || billingStatus === 'cancelled') {
    const res = NextResponse.next();
    res.cookies.set('pending_checkout', '', { path: '/', maxAge: 0 });
    return res;
  }

  if (req.nextUrl.pathname === '/api/health') {
    return NextResponse.next();
  }

  if (req.nextUrl.pathname.startsWith('/api/auth/')) {
    return NextResponse.next();
  }
  // Allow public billing endpoints (checkout returns 401 JSON; webhook used by Stripe)
  if (req.nextUrl.pathname.startsWith('/api/billing/')) {
    return NextResponse.next();
  }

  // Allow public waitlist endpoints
  if (req.nextUrl.pathname.startsWith('/api/waitlist/')) {
    return NextResponse.next();
  }

  // If a pending checkout exists, force user into billing/start, except for auth flows
  const allowedDuringPending = [
    '/billing/start',
    '/register',
    '/login',
    '/verify-email',
    '/forgot-password',
    '/reset-password',
  ];

  if (
    pending &&
    !allowedDuringPending.some((p) => req.nextUrl.pathname.startsWith(p)) &&
    !req.nextUrl.pathname.startsWith('/api/')
  ) {
    return NextResponse.redirect(new URL('/billing/start', req.url));
  }

  return auth(req as any);
}

export const config = {
  matcher: [
    '/((?!terms|privacy|landing|home).)*',
    '/api/:path*',
    '/login',
    '/register',
  ],
};
