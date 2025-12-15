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
      const isOnChat = nextUrl.pathname.startsWith('/');
      const isOnRegister = nextUrl.pathname.startsWith('/register');
      const isOnLogin = nextUrl.pathname.startsWith('/login');
      const isOnLanding = nextUrl.pathname.startsWith('/landing');
      const isOnVerifyEmail = nextUrl.pathname.startsWith('/verify-email');
      const isOnForgotPassword =
        nextUrl.pathname.startsWith('/forgot-password');
      const isOnResetPassword = nextUrl.pathname.startsWith('/reset-password');

      if (isLoggedIn && (isOnLogin || isOnRegister)) {
        // If a pending checkout cookie exists, send user to billing/start first
        const cookie = (nextUrl as unknown as URL).searchParams.get('force');
        const hasPending = (nextUrl as unknown as URL).searchParams.get(
          'pending',
        );
        if (!cookie && !hasPending) {
          // We cannot read cookies here easily; rely on client redirect after login.
        }
        return Response.redirect(new URL('/', nextUrl as unknown as URL));
      }

      if (
        isOnRegister ||
        isOnLogin ||
        isOnLanding ||
        isOnVerifyEmail ||
        isOnForgotPassword ||
        isOnResetPassword
      ) {
        return true; // Always allow access to auth pages
      }

      if (isOnChat) {
        if (isLoggedIn) return true;
        return false; // Redirect unauthenticated users to login page
      }

      if (isLoggedIn) {
        return Response.redirect(new URL('/', nextUrl as unknown as URL));
      }

      return true;
    },
  },
  trustHost: true,
} satisfies NextAuthConfig;
