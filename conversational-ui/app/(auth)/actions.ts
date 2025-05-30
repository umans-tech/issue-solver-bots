'use server';

import { z } from 'zod';
import { nanoid } from 'nanoid';

import { createUser, getUser, createUserWithVerification } from '@/lib/db/queries';
import { sendVerificationEmail } from '@/lib/email';
import { 
  LoginStatus, 
  RegisterStatus, 
  type LoginActionState, 
  type RegisterActionState 
} from './status';

import { signIn } from './auth';
import { ensureDefaultSpace } from '@/lib/db/queries';

const authFormSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
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
