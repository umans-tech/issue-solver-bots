'use client';

import { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { toast } from 'sonner';

import { IconUmansLogo } from '@/components/icons';
import { Button } from '@/components/ui/button';

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams?.get('token');
  
  const [status, setStatus] = useState<'verifying' | 'success' | 'error' | 'pending'>('pending');
  const [isResending, setIsResending] = useState(false);

  useEffect(() => {
    if (token) {
      setStatus('verifying');
      verifyEmail(token);
    }
  }, [token]);

  const verifyEmail = async (verificationToken: string) => {
    try {
      const response = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token: verificationToken }),
      });

      if (response.ok) {
        setStatus('success');
        toast.success('Email verified successfully!');
        // Clear stored email after successful verification
        if (typeof window !== 'undefined') {
          localStorage.removeItem('pendingVerificationEmail');
        }
        // Redirect to login after 3 seconds
        setTimeout(() => {
          router.push('/login');
        }, 3000);
      } else {
        setStatus('error');
        const data = await response.json();
        toast.error(data.error || 'Verification failed');
      }
    } catch (error) {
      console.error('Verification error:', error);
      setStatus('error');
      toast.error('Verification failed');
    }
  };

  const resendVerification = async () => {
    setIsResending(true);
    try {
      // Get email from localStorage if available
      const email = typeof window !== 'undefined' 
        ? localStorage.getItem('pendingVerificationEmail') 
        : null;

      const response = await fetch('/api/auth/resend-verification', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      if (response.ok) {
        toast.success('Verification email sent!');
      } else {
        const data = await response.json();
        toast.error(data.error || 'Failed to resend verification email');
      }
    } catch (error) {
      console.error('Resend error:', error);
      toast.error('Failed to resend verification email');
    } finally {
      setIsResending(false);
    }
  };

  return (
    <div className="flex h-dvh w-screen items-start pt-12 md:pt-0 md:items-center justify-center bg-background">
      <div className="w-full max-w-md overflow-hidden rounded-2xl flex flex-col gap-12">
        <div className="flex flex-col items-center justify-center gap-2 px-4 text-center sm:px-16">
          <div className="mb-4">
            <IconUmansLogo className="h-16 w-auto" />
          </div>
          
          {status === 'pending' && (
            <>
              <h3 className="text-xl font-semibold dark:text-zinc-50">Check Your Email</h3>
              <p className="text-sm text-gray-500 dark:text-zinc-400">
                We've sent a verification email to your address. Please click the link in the email to verify your account.
              </p>
              <div className="mt-6">
                <Button 
                  onClick={resendVerification} 
                  disabled={isResending}
                  variant="outline"
                >
                  {isResending ? 'Sending...' : 'Resend Verification Email'}
                </Button>
              </div>
            </>
          )}

          {status === 'verifying' && (
            <>
              <h3 className="text-xl font-semibold dark:text-zinc-50">Verifying Email...</h3>
              <p className="text-sm text-gray-500 dark:text-zinc-400">
                Please wait while we verify your email address.
              </p>
            </>
          )}

          {status === 'success' && (
            <>
              <h3 className="text-xl font-semibold text-green-600 dark:text-green-400">Email Verified! ✅</h3>
              <p className="text-sm text-gray-500 dark:text-zinc-400">
                Your email has been successfully verified. You will be redirected to the login page shortly.
              </p>
              <div className="mt-6">
                <Button onClick={() => router.push('/login')}>
                  Continue to Login
                </Button>
              </div>
            </>
          )}

          {status === 'error' && (
            <>
              <h3 className="text-xl font-semibold text-red-600 dark:text-red-400">Verification Failed</h3>
              <p className="text-sm text-gray-500 dark:text-zinc-400">
                The verification link may be invalid or expired. Please try requesting a new verification email.
              </p>
              <div className="mt-6 flex gap-4">
                <Button 
                  onClick={resendVerification} 
                  disabled={isResending}
                  variant="outline"
                >
                  {isResending ? 'Sending...' : 'Resend Verification Email'}
                </Button>
                <Button onClick={() => router.push('/register')} variant="outline">
                  Back to Register
                </Button>
              </div>
            </>
          )}
        </div>
        
        <div className="text-center px-4 sm:px-16">
          <p className="text-sm text-gray-600 dark:text-zinc-400">
            {'Already verified? '}
            <Link
              href="/login"
              className="font-semibold text-gray-800 hover:underline dark:text-zinc-200"
            >
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={
      <div className="flex h-dvh w-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <IconUmansLogo className="h-16 w-auto" />
          <p className="text-sm text-gray-500 dark:text-zinc-400">Loading...</p>
        </div>
      </div>
    }>
      <VerifyEmailContent />
    </Suspense>
  );
} 