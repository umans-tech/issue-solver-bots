'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useActionState, useEffect, useState } from 'react';
import { toast } from 'sonner';

import { AuthForm } from '@/components/auth-form';
import { IconUmansLogo } from '@/components/icons';
import { SubmitButton } from '@/components/submit-button';

import { login } from '../actions';
import { LoginStatus, type LoginActionState } from '../status';

export default function Page() {
  const router = useRouter();

  const [email, setEmail] = useState('');
  const [isSuccessful, setIsSuccessful] = useState(false);

  const [state, formAction] = useActionState<LoginActionState, FormData>(
    login,
    {
      status: LoginStatus.IDLE,
    },
  );

  useEffect(() => {
    if (state.status === LoginStatus.EMAIL_NOT_VERIFIED) {
      toast.error(state.error || 'Please verify your email address before signing in.', {
        action: {
          label: 'Resend Verification',
          onClick: () => router.push('/verify-email'),
        },
      });
    } else if (state.status === LoginStatus.FAILED) {
      toast.error(state.error || 'Invalid credentials');
    } else if (state.status === LoginStatus.INVALID_DATA) {
      toast.error(state.error || 'Please enter valid credentials.');
    } else if (state.status === LoginStatus.SUCCESS) {
      setIsSuccessful(true);
      router.refresh();
    }
  }, [state, router]);

  const handleSubmit = (formData: FormData) => {
    setEmail(formData.get('email') as string);
    formAction(formData);
  };

  return (
    <div className="flex h-dvh w-screen items-start pt-12 md:pt-0 md:items-center justify-center bg-background">
      <div className="w-full max-w-md overflow-hidden rounded-2xl flex flex-col gap-12">
        <div className="flex flex-col items-center justify-center gap-2 px-4 text-center sm:px-16">
          <div className="mb-4">
            <IconUmansLogo className="h-16 w-auto" />
          </div>
          <h3 className="text-xl font-semibold dark:text-zinc-50">Sign In</h3>
          <p className="text-sm text-gray-500 dark:text-zinc-400">
            Use your email and password to sign in
          </p>
        </div>
        <AuthForm action={handleSubmit} defaultEmail={email}>
          <SubmitButton isSuccessful={isSuccessful}>Sign in</SubmitButton>
          <p className="text-center text-sm text-gray-600 mt-4 dark:text-zinc-400">
            {"Don't have an account? "}
            <Link
              href="/register"
              className="font-semibold text-gray-800 hover:underline dark:text-zinc-200"
            >
              Sign up
            </Link>
            {' for free.'}
          </p>
        </AuthForm>
      </div>
    </div>
  );
}
