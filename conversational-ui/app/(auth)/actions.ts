'use server';

import { z } from 'zod';
import { nanoid } from 'nanoid';
import { genSaltSync, hashSync } from 'bcrypt-ts';

import { createUser, getUser, createUserWithVerification, getUserByVerificationToken } from '@/lib/db/queries';
import { sendVerificationEmail, sendPasswordResetEmail } from '@/lib/email';
import { 
  LoginStatus, 
  RegisterStatus,
  PasswordResetStatus,
  type LoginActionState, 
  type RegisterActionState,
  type PasswordResetActionState
} from './status';

import { signIn } from './auth';
import { ensureDefaultSpace } from '@/lib/db/queries';

// Reuse existing database connection pattern
import { eq } from 'drizzle-orm';
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import { user } from '@/lib/db/schema';

const client = postgres(process.env.POSTGRES_URL!);
const db = drizzle(client);

const authFormSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
});

const emailSchema = z.object({
  email: z.string().email(),
});

// Constants for consistent error responses
const INVALID_CREDENTIALS_RESPONSE = { 
  status: LoginStatus.FAILED, 
  error: 'Invalid credentials' 
};

const REGISTRATION_FAILED_RESPONSE = {
  status: RegisterStatus.FAILED,
  error: 'Failed to create account. Please try again.'
};

const INVALID_FORM_DATA_RESPONSE = {
  status: RegisterStatus.INVALID_DATA,
  error: 'Please enter a valid email and a password with at least 6 characters.'
};

export const login = async (
  _: LoginActionState,
  formData: FormData,
): Promise<LoginActionState> => {
  try {
    const validatedData = authFormSchema.parse({
      email: formData.get('email'),
      password: formData.get('password'),
    });

    // First, check if user exists
    const [user] = await getUser(validatedData.email);
    
    if (!user) {
      return INVALID_CREDENTIALS_RESPONSE;
    }

    // Check if this is an OAuth user (no password)
    if (!user.password) {
      return INVALID_CREDENTIALS_RESPONSE;
    }

    // Check password first before revealing verification status
    const { compare } = await import('bcrypt-ts');
    const passwordsMatch = await compare(validatedData.password, user.password);
    
    if (!passwordsMatch) {
      return INVALID_CREDENTIALS_RESPONSE;
    }

    // Only reveal verification status if credentials are correct
    if (!user.emailVerified) {
      return { 
        status: LoginStatus.EMAIL_NOT_VERIFIED, 
        error: 'Please verify your email address before signing in. Check your inbox for the verification link.' 
      };
    }

    // If all checks pass, attempt to sign in
    await signIn('credentials', {
      email: validatedData.email,
      password: validatedData.password,
      redirect: false,
    });

    return { status: LoginStatus.SUCCESS };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { 
        status: LoginStatus.INVALID_DATA,
        error: 'Please enter a valid email and password.'
      };
    }

    console.error('Login error:', error);
    return INVALID_CREDENTIALS_RESPONSE;
  }
};

export const register = async (
  _: RegisterActionState,
  formData: FormData,
): Promise<RegisterActionState> => {
  try {
    const validatedData = authFormSchema.parse({
      email: formData.get('email'),
      password: formData.get('password'),
    });

    const [user] = await getUser(validatedData.email);

    if (user) {
      // Don't reveal whether it's OAuth or password user for security
      return { 
        status: RegisterStatus.USER_EXISTS,
        error: 'An account with this email already exists.'
      };
    }

    // Generate verification token
    const verificationToken = nanoid(64);

    // Create the user with verification token (unverified)
    await createUserWithVerification(validatedData.email, validatedData.password, verificationToken);

    // Send verification email
    try {
      await sendVerificationEmail(validatedData.email, verificationToken);
    } catch (emailError) {
      console.error('Failed to send verification email:', emailError);
      return REGISTRATION_FAILED_RESPONSE;
    }

    return { status: RegisterStatus.VERIFICATION_SENT };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return INVALID_FORM_DATA_RESPONSE;
    }

    console.error('Registration error:', error);
    return REGISTRATION_FAILED_RESPONSE;
  }
};

// Simplified password reset - combines both request and reset
export const passwordReset = async (
  _: PasswordResetActionState,
  formData: FormData,
): Promise<PasswordResetActionState> => {
  try {
    const email = formData.get('email') as string;
    const token = formData.get('token') as string;
    const newPassword = formData.get('password') as string;

    // If no token, this is a reset request
    if (!token) {
      const validatedData = emailSchema.parse({ email });

      // Always return success for security (don't reveal if user exists)
      try {
        const [existingUser] = await getUser(validatedData.email);
        if (existingUser) {
          const resetToken = nanoid(64);
          
          // Update user with reset token (reuse existing field)
          await db
            .update(user)
            .set({ emailVerificationToken: resetToken })
            .where(eq(user.id, existingUser.id));

          await sendPasswordResetEmail(validatedData.email, resetToken);
        }
      } catch (error) {
        console.error('Password reset error:', error);
      }

      return { 
        status: PasswordResetStatus.SUCCESS,
        message: 'If an account with that email exists, you will receive reset instructions.'
      };
    }

    // If token exists, this is password update
    if (!newPassword || newPassword.length < 6) {
      return {
        status: PasswordResetStatus.INVALID_DATA,
        error: 'Password must be at least 6 characters.'
      };
    }

    const [userRecord] = await getUserByVerificationToken(token);
    if (!userRecord || !userRecord.password) {
      return {
        status: PasswordResetStatus.FAILED,
        error: 'Invalid reset link or account uses Google sign-in.'
      };
    }

    // Update password and clear token
    const salt = genSaltSync(10);
    const hashedPassword = hashSync(newPassword, salt);

    await db
      .update(user)
      .set({ 
        password: hashedPassword,
        emailVerificationToken: null 
      })
      .where(eq(user.id, userRecord.id));

    // Auto sign-in the user after successful password reset
    try {
      await signIn('credentials', {
        email: userRecord.email,
        password: newPassword,
        redirect: false,
      });
      
      return { 
        status: PasswordResetStatus.SUCCESS,
        message: 'Password reset successfully! Signing you in...'
      };
    } catch (signInError) {
      console.error('Auto sign-in failed after password reset:', signInError);
      // Still return success since password was reset
      return { 
        status: PasswordResetStatus.SUCCESS,
        message: 'Password reset successfully! Please sign in with your new password.'
      };
    }
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { 
        status: PasswordResetStatus.INVALID_DATA,
        error: 'Please enter a valid email address.'
      };
    }

    console.error('Password reset error:', error);
    return { 
      status: PasswordResetStatus.FAILED,
      error: 'Something went wrong. Please try again.'
    };
  }
};
