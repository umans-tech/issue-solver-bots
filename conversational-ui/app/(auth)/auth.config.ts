import type { NextAuthConfig } from 'next-auth';

export const authConfig = {
  pages: {
    signIn: '/login',
    newUser: '/',
  },
  providers: [
    // added later in auth.ts since it requires bcrypt which is only compatible with Node.js
    // while this file is also used in non-Node.js environments
  ],
  callbacks: {
    authorized({ auth, request: { nextUrl } }) {
      const isLoggedIn = !!auth?.user;
      const isOnRegister = nextUrl.pathname.startsWith('/register');
      const isOnLogin = nextUrl.pathname.startsWith('/login');
      const isOnLanding = nextUrl.pathname.startsWith('/landing');
      const isOnVerifyEmail = nextUrl.pathname.startsWith('/verify-email');
      const isOnForgotPassword = nextUrl.pathname.startsWith('/forgot-password');
      const isOnResetPassword = nextUrl.pathname.startsWith('/reset-password');
      const isOnOnboarding = nextUrl.pathname.startsWith('/onboarding');
      
      // Auth pages that don't require login
      const isOnAuthPage = isOnRegister || isOnLogin || isOnLanding || isOnVerifyEmail || isOnForgotPassword || isOnResetPassword;

      const needsOnboarding = isLoggedIn && (auth?.user as any)?.hasCompletedOnboarding === false;

      // Debug logging
      console.log('🔐 Auth check:', {
        pathname: nextUrl.pathname,
        isLoggedIn,
        hasCompletedOnboarding: (auth?.user as any)?.hasCompletedOnboarding,
        needsOnboarding,
        isOnOnboarding
      });

      // Redirect logged in users away from login/register pages
      if (isLoggedIn && (isOnLogin || isOnRegister)) {
        return Response.redirect(new URL('/', nextUrl as unknown as URL));
      }

      // Redirect users who need onboarding (unless they're already on onboarding page)
      if (needsOnboarding && !isOnOnboarding) {
        console.log('🔄 Redirecting to onboarding');
        return Response.redirect(new URL('/onboarding', nextUrl as unknown as URL));
      }

      // Always allow access to auth pages and onboarding
      if (isOnAuthPage || isOnOnboarding) {
        return true;
      }

      // For all other pages, require authentication
      if (isLoggedIn) {
        return true;
      }

      // Redirect unauthenticated users to login
      return false;
    },
  },
  trustHost: true,
} satisfies NextAuthConfig;
