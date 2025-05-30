'use client';

import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useActionState, useEffect, useState, Suspense } from 'react';
import { toast } from 'sonner';
import Form from 'next/form';

import { IconUmansLogo } from '@/components/icons';
import { SubmitButton } from '@/components/submit-button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

import { passwordReset } from '../actions';
import { PasswordResetStatus, type PasswordResetActionState } from '../status';

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams?.get('token');

  const [state, formAction] = useActionState<PasswordResetActionState, FormData>(
    passwordReset,
    {
      status: PasswordResetStatus.IDLE,
    },
  );

  useEffect(() => {
    if (state.status === PasswordResetStatus.SUCCESS) {
      toast.success('Password reset successfully! Signing you in...');
      setTimeout(() => {
        router.push('/');
      }, 2000);
    } else if (state.status === PasswordResetStatus.FAILED) {
      toast.error(state.error || 'Failed to reset password');
    } else if (state.status === PasswordResetStatus.INVALID_DATA) {
      toast.error(state.error || 'Please enter a valid password.');
    }
  }, [state, router]);

  const handleSubmit = (formData: FormData) => {
    formData.append('token', token || '');
    formAction(formData);
  };

  if (!token) {
    return (
      <div className="flex h-dvh w-screen items-center justify-center bg-background">
        <div className="w-full max-w-md overflow-hidden rounded-2xl flex flex-col gap-12">
          <div className="flex flex-col items-center justify-center gap-2 px-4 text-center sm:px-16">
            <div className="mb-4">
              <IconUmansLogo className="h-16 w-auto" />
            </div>
            <h3 className="text-xl font-semibold text-red-600 dark:text-red-400">Invalid Reset Link</h3>
            <p className="text-sm text-gray-500 dark:text-zinc-400">
              This password reset link is invalid or has expired.
            </p>
            <Link
              href="/forgot-password"
              className="mt-4 font-semibold text-gray-800 hover:underline dark:text-zinc-200"
            >
              Request a new reset link
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-dvh w-screen items-start pt-12 md:pt-0 md:items-center justify-center bg-background">
      <div className="w-full max-w-md overflow-hidden rounded-2xl flex flex-col gap-12">
        <div className="flex flex-col items-center justify-center gap-2 px-4 text-center sm:px-16">
          <div className="mb-4">
            <IconUmansLogo className="h-16 w-auto" />
          </div>
          <h3 className="text-xl font-semibold dark:text-zinc-50">Reset Password</h3>
          <p className="text-sm text-gray-500 dark:text-zinc-400">
            Enter your new password below
          </p>
        </div>

        <div className="flex flex-col gap-4 px-4 sm:px-16">
          <Form action={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label
                htmlFor="password"
                className="text-zinc-600 font-normal dark:text-zinc-400"
              >
                New Password
              </Label>

              <Input
                id="password"
                name="password"
                className="bg-muted text-md md:text-sm"
                type="password"
                required
                autoFocus
                minLength={6}
              />
            </div>

            <SubmitButton isSuccessful={false}>
              Reset Password
            </SubmitButton>

            <div className="text-center text-sm text-gray-600 dark:text-zinc-400">
              <Link
                href="/login"
                className="font-semibold text-gray-800 hover:underline dark:text-zinc-200"
              >
                Back to Sign In
              </Link>
            </div>
          </Form>
        </div>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="flex h-dvh w-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <IconUmansLogo className="h-16 w-auto" />
          <p className="text-sm text-gray-500 dark:text-zinc-400">Loading...</p>
        </div>
      </div>
    }>
      <ResetPasswordContent />
    </Suspense>
  );
} 