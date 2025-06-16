import type { NextAuthConfig } from 'next-auth';

export const authConfig = {
  pages: {
    signIn: '/login',
    newUser: '/onboarding',
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
      
      const isOnAuthPage = isOnRegister || isOnLogin || isOnLanding || isOnVerifyEmail || isOnForgotPassword || isOnResetPassword;

      if (isLoggedIn && (isOnLogin || isOnRegister)) {
        return Response.redirect(new URL('/', nextUrl as unknown as URL));
      }

      if (isOnAuthPage || isOnOnboarding) {
        return true;
      }

      if (isLoggedIn) {
        return true;
      }

      return false;
    },
  },
  trustHost: true,
} satisfies NextAuthConfig;
