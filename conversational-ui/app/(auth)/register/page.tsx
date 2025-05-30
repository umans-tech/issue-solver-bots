'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useActionState, useEffect, useState } from 'react';
import { toast } from 'sonner';

import { AuthForm } from '@/components/auth-form';
import { IconUmansLogo } from '@/components/icons';
import { SubmitButton } from '@/components/submit-button';

import { register } from '../actions';
import { RegisterStatus, type RegisterActionState } from '../status';

export default function Page() {
  const router = useRouter();

  const [email, setEmail] = useState('');
  const [isSuccessful, setIsSuccessful] = useState(false);

  const [state, formAction] = useActionState<RegisterActionState, FormData>(
    register,
    {
      status: RegisterStatus.IDLE,
    },
  );

  useEffect(() => {
    if (state.status === RegisterStatus.USER_EXISTS) {
      toast.error(state.error || 'An account with this email already exists.', {
        action: {
          label: 'Sign In',
          onClick: () => router.push('/login'),
        },
      });
    } else if (state.status === RegisterStatus.FAILED) {
      toast.error(state.error || 'Failed to create account');
    } else if (state.status === RegisterStatus.INVALID_DATA) {
      toast.error(state.error || 'Please enter valid information');
    } else if (state.status === RegisterStatus.SUCCESS) {
      toast.success('Account created successfully');
      setIsSuccessful(true);
      router.refresh();
    } else if (state.status === RegisterStatus.VERIFICATION_SENT) {
      toast.success('Verification email sent! Please check your email.');
      setIsSuccessful(true);
      // Store email for verification page
      if (typeof window !== 'undefined') {
        localStorage.setItem('pendingVerificationEmail', email);
      }
      router.push('/verify-email');
    }
  }, [state, router, email]);

  const handleSubmit = (formData: FormData) => {
    setEmail(formData.get('email') as string);
    formAction(formData);
  };

  return (
    <div className="flex h-dvh w-screen items-start pt-12 md:pt-0 md:items-center justify-center bg-background">
      <div className="w-full max-w-md overflow-hidden rounded-2xl gap-12 flex flex-col">
        <div className="flex flex-col items-center justify-center gap-2 px-4 text-center sm:px-16">
          <div className="mb-4">
            <IconUmansLogo className="h-16 w-auto" />
          </div>
          <h3 className="text-xl font-semibold dark:text-zinc-50">Sign Up</h3>
          <p className="text-sm text-gray-500 dark:text-zinc-400">
            Create an account with your email and password
          </p>
        </div>
        <AuthForm action={handleSubmit} defaultEmail={email} showTerms={true}>
          <SubmitButton isSuccessful={isSuccessful}>Sign Up</SubmitButton>
          <p className="text-center text-sm text-gray-600 mt-4 dark:text-zinc-400">
            {'Already have an account? '}
            <Link
              href="/login"
              className="font-semibold text-gray-800 hover:underline dark:text-zinc-200"
            >
              Sign in
            </Link>
            {' instead.'}
          </p>
        </AuthForm>
      </div>
    </div>
  );
}
