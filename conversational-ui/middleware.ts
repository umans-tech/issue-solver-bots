import { NextRequest, NextResponse } from 'next/server';
import NextAuth from 'next-auth';
import { authConfig } from '@/app/(auth)/auth.config';

const { auth } = NextAuth(authConfig);

export default function middleware(req: NextRequest) {
    if (req.nextUrl.pathname === '/api/health') {
        return NextResponse.next();
    }
    return auth(req as any)
}

export const config = {
    matcher: [
        '/((?!terms|privacy|landing).)*',
        '/api/:path*',
        '/login',
        '/register',
    ],
};
