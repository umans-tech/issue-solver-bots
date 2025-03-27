import NextAuth from 'next-auth';

import { authConfig } from '@/app/(auth)/auth.config';

export default NextAuth(authConfig).auth;

export const config = {
  // Matcher ignoring /terms and /privacy pages to make them publicly accessible
  matcher: ['/((?!terms|privacy).)*', '/api/:path*', '/login', '/register'],
};
