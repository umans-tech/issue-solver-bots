'use server';

import { z } from 'zod';
import { compare } from 'bcrypt-ts';

import { createUser, getUser } from '@/lib/db/queries';
import { ensureDefaultSpace } from '@/lib/db/queries';

const authFormSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
});

export interface LoginActionState {
  status: 'idle' | 'in_progress' | 'success' | 'failed' | 'invalid_data';
  message?: string;
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

    // Validate credentials on server side
    const users = await getUser(validatedData.email);
    if (users.length === 0) {
      return { status: 'failed', message: 'Invalid credentials!' };
    }

    const passwordsMatch = await compare(validatedData.password, users[0].password!);
    if (!passwordsMatch) {
      return { status: 'failed', message: 'Invalid credentials!' };
    }

    // Credentials are valid, return success
    // The client side will handle the actual signIn call
    return { status: 'success' };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { status: 'invalid_data' };
    }

    console.error('Login error:', error);
    return { status: 'failed', message: 'Login failed. Please try again.' };
  }
};

export interface RegisterActionState {
  status:
    | 'idle'
    | 'in_progress'
    | 'success'
    | 'failed'
    | 'user_exists'
    | 'invalid_data';
  message?: string;
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
      return { status: 'user_exists', message: 'User already exists' } as RegisterActionState;
    }
    
    // Create the user
    await createUser(validatedData.email, validatedData.password);
    
    // Get the newly created user to access their ID
    const [newUser] = await getUser(validatedData.email);
    
    // Create a default space for the user
    if (newUser && newUser.id) {
      await ensureDefaultSpace(newUser.id);
    }
    
    // Return success, client side will handle signIn
    return { status: 'success' };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { status: 'invalid_data' };
    }

    console.error('Register error:', error);
    return { status: 'failed', message: 'Registration failed. Please try again.' };
  }
};
