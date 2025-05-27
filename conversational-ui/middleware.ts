import { NextResponse } from 'next/server';
import { withAuth } from 'next-auth/middleware';

export default withAuth(
  function middleware(req) {
    if (req.nextUrl.pathname === '/api/health') {
      return NextResponse.next();
    }
    
    const token = req.nextauth.token;
    const isLoggedIn = !!token;
    const isOnChat = req.nextUrl.pathname.startsWith('/');
    const isOnRegister = req.nextUrl.pathname.startsWith('/register');
    const isOnLogin = req.nextUrl.pathname.startsWith('/login');
    const isOnLanding = req.nextUrl.pathname.startsWith('/landing');

    if (isLoggedIn && (isOnLogin || isOnRegister)) {
      return NextResponse.redirect(new URL('/', req.url));
    }

    if (isOnRegister || isOnLogin || isOnLanding) {
      return NextResponse.next(); // Allow access to register, login, and landing pages
    }

    if (isOnChat) {
      if (isLoggedIn) return NextResponse.next();
      return NextResponse.redirect(new URL('/login', req.url)); // Redirect unauthenticated users to login page
    }

    if (isLoggedIn) {
      return NextResponse.redirect(new URL('/', req.url));
    }

    return NextResponse.next();
  },
  {
    callbacks: {
      authorized: ({ token }) => {
        // This allows the middleware to run on all requests
        // The actual authorization logic is handled in the middleware function above
        return true;
      },
    },
  }
);

export const config = {
    matcher: [
        '/((?!terms|privacy|landing).)*',
        '/api/:path*',
        '/login',
        '/register',
    ],
};
