'use server';

import { z } from 'zod';
import { nanoid } from 'nanoid';

import { createUser, getUser, createUserWithVerification } from '@/lib/db/queries';
import { sendVerificationEmail } from '@/lib/email';

import { signIn } from './auth';
import { ensureDefaultSpace } from '@/lib/db/queries';

const authFormSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
});

export interface LoginActionState {
  status: 'idle' | 'in_progress' | 'success' | 'failed' | 'invalid_data';
}

export const login = async (
  _: LoginActionState,
  formData: FormData,
): Promise<LoginActionState> => {
  try {
    const validatedData = authFormSchema.parse({
      email: formData.get('email'),
      password: formData.get('password'),
    });

    await signIn('credentials', {
      email: validatedData.email,
      password: validatedData.password,
      redirect: false,
    });

    return { status: 'success' };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { status: 'invalid_data' };
    }

    return { status: 'failed' };
  }
};

export interface RegisterActionState {
  status: 
    | 'idle' 
    | 'in_progress' 
    | 'success' 
    | 'failed' 
    | 'invalid_data'
    | 'user_exists'
    | 'oauth_user_exists'
    | 'verification_sent';
}

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
      if (!user.password) {
        // User exists but has no password (OAuth user)
        return { status: 'oauth_user_exists' } as RegisterActionState;
      }
      // User exists with password
      return { status: 'user_exists' } as RegisterActionState;
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
      // You might want to delete the user here if email fails
      return { status: 'failed' };
    }

    return { status: 'verification_sent' };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { status: 'invalid_data' };
    }

    return { status: 'failed' };
  }
};
