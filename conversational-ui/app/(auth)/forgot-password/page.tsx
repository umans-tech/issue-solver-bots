'use client';

import Link from 'next/link';
import { useActionState, useEffect, useState } from 'react';
import { toast } from 'sonner';
import Form from 'next/form';

import { IconUmansLogo } from '@/components/icons';
import { SubmitButton } from '@/components/submit-button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';

import { passwordReset } from '../actions';
import { PasswordResetStatus, type PasswordResetActionState } from '../status';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');

  const [state, formAction] = useActionState<PasswordResetActionState, FormData>(
    passwordReset,
    {
      status: PasswordResetStatus.IDLE,
    },
  );

  useEffect(() => {
    if (state.status === PasswordResetStatus.SUCCESS) {
      toast.success(state.message || 'Password reset instructions sent to your email.');
    } else if (state.status === PasswordResetStatus.FAILED) {
      toast.error(state.error || 'Failed to send reset email');
    } else if (state.status === PasswordResetStatus.INVALID_DATA) {
      toast.error(state.error || 'Please enter a valid email address.');
    }
  }, [state]);

  const handleSubmit = (formData: FormData) => {
    setEmail(formData.get('email') as string);
    formAction(formData);
  };

  const handleSendAgain = () => {
    if (email) {
      const formData = new FormData();
      formData.append('email', email);
      formAction(formData);
    }
  };

  const isInstructionsSent = state.status === PasswordResetStatus.SUCCESS;

  return (
    <div className="flex h-dvh w-screen items-start pt-12 md:pt-0 md:items-center justify-center bg-background">
      <div className="w-full max-w-md overflow-hidden rounded-2xl flex flex-col gap-12">
        <div className="flex flex-col items-center justify-center gap-2 px-4 text-center sm:px-16">
          <div className="mb-4">
            <IconUmansLogo className="h-16 w-auto" />
          </div>
          <h3 className="text-xl font-semibold dark:text-zinc-50">
            {isInstructionsSent ? 'Check Your Email' : 'Forgot Password'}
          </h3>
          <p className="text-sm text-gray-500 dark:text-zinc-400">
            {isInstructionsSent 
              ? 'We\'ve sent password reset instructions to your email address.'
              : 'Enter your email address and we\'ll send you instructions to reset your password'
            }
          </p>
        </div>

        <div className="flex flex-col gap-4 px-4 sm:px-16">
          <Form action={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-2">
              <Label
                htmlFor="email"
                className="text-zinc-600 font-normal dark:text-zinc-400"
              >
                Email Address
              </Label>

              <Input
                id="email"
                name="email"
                className="bg-muted text-md md:text-sm"
                type="email"
                placeholder="user@acme.com"
                autoComplete="email"
                required
                autoFocus={!isInstructionsSent}
                defaultValue={email}
                readOnly={isInstructionsSent}
                disabled={isInstructionsSent}
              />
            </div>

            {!isInstructionsSent ? (
              <SubmitButton isSuccessful={false}>
                Send Reset Instructions
              </SubmitButton>
            ) : (
              <div className="flex flex-col gap-2">
                <Button 
                  type="button" 
                  disabled 
                  className="bg-green-600 hover:bg-green-600"
                >
                  ✓ Instructions Sent
                </Button>
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={handleSendAgain}
                  className="text-sm"
                >
                  Send Again
                </Button>
              </div>
            )}

            <div className="flex flex-col gap-2 text-center text-sm text-gray-600 dark:text-zinc-400">
              <Link
                href="/login"
                className="font-semibold text-gray-800 hover:underline dark:text-zinc-200"
              >
                Back to Sign In
              </Link>
              <span>
                {"Don't have an account? "}
                <Link
                  href="/register"
                  className="font-semibold text-gray-800 hover:underline dark:text-zinc-200"
                >
                  Sign up
                </Link>
              </span>
            </div>
          </Form>
        </div>
      </div>
    </div>
  );
} 