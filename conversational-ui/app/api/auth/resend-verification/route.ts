import { NextResponse } from 'next/server';
import { nanoid } from 'nanoid';
import { getUser } from '@/lib/db/queries';
import { sendVerificationEmail } from '@/lib/email';
import { eq } from 'drizzle-orm';
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import { user } from '@/lib/db/schema';

// biome-ignore lint: Forbidden non-null assertion.
const client = postgres(process.env.POSTGRES_URL!);
const db = drizzle(client);

export async function POST(request: Request) {
  try {
    let email: string;

    // Try to get email from request body, fallback to URL search params
    try {
      const body = await request.json();
      email = body.email;
    } catch {
      // If no JSON body, try to get from URL search params
      const url = new URL(request.url);
      email = url.searchParams.get('email') || '';
    }

    if (!email) {
      return NextResponse.json({ error: 'Email is required' }, { status: 400 });
    }

    // Find user by email
    const [existingUser] = await getUser(email);

    if (!existingUser) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 });
    }

    if (existingUser.emailVerified) {
      return NextResponse.json(
        { error: 'Email is already verified' },
        { status: 400 },
      );
    }

    // Generate new verification token
    const newVerificationToken = nanoid(64);

    // Update user with new verification token
    await db
      .update(user)
      .set({ emailVerificationToken: newVerificationToken })
      .where(eq(user.id, existingUser.id));

    // Send verification email
    await sendVerificationEmail(existingUser.email, newVerificationToken);

    return NextResponse.json(
      { message: 'Verification email sent successfully' },
      { status: 200 },
    );
  } catch (error) {
    console.error('Resend verification error:', error);
    return NextResponse.json(
      { error: 'Failed to resend verification email' },
      { status: 500 },
    );
  }
}
