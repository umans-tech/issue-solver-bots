import { NextRequest, NextResponse } from 'next/server';
import NextAuth from 'next-auth';
import { authConfig } from '@/app/(auth)/auth.config';

const { auth } = NextAuth(authConfig);

export default async function middleware(req: NextRequest) {
  if (req.nextUrl.pathname === '/api/health') {
    return NextResponse.next();
  }
  
  if (req.nextUrl.pathname.startsWith('/api/auth/')) {
    return NextResponse.next();
  }
  
  // Handle onboarding redirect for main pages
  if (req.nextUrl.pathname === '/' || req.nextUrl.pathname.startsWith('/chat') || req.nextUrl.pathname.startsWith('/tasks') || req.nextUrl.pathname.startsWith('/integrations')) {
    try {
      const sessionResponse = await fetch(new URL('/api/auth/session', req.url), {
        headers: {
          cookie: req.headers.get('cookie') || '',
        },
      });
      
      if (sessionResponse.ok) {
        const session = await sessionResponse.json();
        
        if (session?.user?.id && session.user.hasCompletedOnboarding === false) {
          return NextResponse.redirect(new URL('/onboarding', req.url));
        }
      }
    } catch (error) {
      console.error('Error checking session in middleware:', error);
    }
  }
  
  return auth(req as any);
}

export const config = {
  matcher: [
    '/',
    '/((?!terms|privacy|landing|_next|favicon|api/auth).)*',
    '/api/:path*',
  ],
};
