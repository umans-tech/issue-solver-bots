'use client';

import Link from 'next/link';
import {useRouter} from 'next/navigation';
import {useActionState, useEffect, useState} from 'react';
import {toast} from 'sonner';
import { signIn } from 'next-auth/react';

import {AuthForm} from '@/components/auth-form';
import {IconUmansLogo} from '@/components/icons';
import {SubmitButton} from '@/components/submit-button';
import { GoogleSignInButton } from '@/components/google-signin-button';
import { AuthDivider } from '@/components/auth-divider';

import {register, type RegisterActionState} from '../actions';

export default function Page() {
    const router = useRouter();

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [isSuccessful, setIsSuccessful] = useState(false);

    const [state, formAction] = useActionState<RegisterActionState, FormData>(
        register,
        {
            status: 'idle',
        },
    );

    useEffect(() => {
        if (state.status === 'user_exists') {
            toast.error(state.message || 'Account already exists');
        } else if (state.status === 'failed') {
            toast.error(state.message || 'Failed to create account');
        } else if (state.status === 'invalid_data') {
            toast.error('Failed validating your submission!');
        } else if (state.status === 'success') {
            // Server registration passed, now sign in with NextAuth
            handleNextAuthSignIn();
        }
    }, [state.status, state.message]);

    const handleNextAuthSignIn = async () => {
        try {
            const result = await signIn('credentials', {
                email,
                password,
                redirect: false,
            });

            if (result?.error) {
                toast.error('Account created but failed to sign in. Please try signing in manually.');
            } else if (result?.ok) {
                setIsSuccessful(true);
                toast.success('Account created and signed in successfully!');
                router.push('/');
            }
        } catch (error) {
            console.error('NextAuth sign in error after registration:', error);
            toast.error('Account created but failed to sign in. Please try signing in manually.');
        }
    };

    const handleSubmit = (formData: FormData) => {
        setEmail(formData.get('email') as string);
        setPassword(formData.get('password') as string);
        formAction(formData);
    };

    return (
        <div className="flex h-dvh w-screen items-start pt-12 md:pt-0 md:items-center justify-center bg-background">
            <div className="w-full max-w-md overflow-hidden rounded-2xl gap-12 flex flex-col">
                <div className="flex flex-col items-center justify-center gap-2 px-4 text-center sm:px-16">
                    <div className="mb-4">
                        <IconUmansLogo className="h-16 w-auto"/>
                    </div>
                    <h3 className="text-xl font-semibold dark:text-zinc-50">Sign Up</h3>
                    <p className="text-sm text-gray-500 dark:text-zinc-400">
                        Create an account with your email and password
                    </p>
                </div>
                
                <div className="flex flex-col gap-4 px-4 sm:px-16">
                    <GoogleSignInButton text="Sign up with Google" />
                    <AuthDivider />
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
