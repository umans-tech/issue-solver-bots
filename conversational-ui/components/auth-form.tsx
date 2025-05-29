import Form from 'next/form';
import Link from 'next/link';

import { Input } from './ui/input';
import { Label } from './ui/label';
import { GoogleSigninButton } from './google-signin-button';

export function AuthForm({
  action,
  children,
  defaultEmail = '',
  showTerms = false,
}: {
  action: NonNullable<
    string | ((formData: FormData) => void | Promise<void>) | undefined
  >;
  children: React.ReactNode;
  defaultEmail?: string;
  showTerms?: boolean;
}) {
  return (
    <div className="flex flex-col gap-4 px-4 sm:px-16">
      {/* Google Sign-in Button */}
      <GoogleSigninButton />

      {/* Divider */}
      <div className="relative flex items-center">
        <div className="flex-grow border-t border-gray-300 dark:border-gray-600" />
        <span className="mx-4 text-sm text-gray-500 dark:text-gray-400">
          or
        </span>
        <div className="flex-grow border-t border-gray-300 dark:border-gray-600" />
      </div>

      {/* Email/Password Form */}
      <Form action={action} className="flex flex-col gap-4">
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
            autoFocus
            defaultValue={defaultEmail}
          />
        </div>

        <div className="flex flex-col gap-2">
          <Label
            htmlFor="password"
            className="text-zinc-600 font-normal dark:text-zinc-400"
          >
            Password
          </Label>

          <Input
            id="password"
            name="password"
            className="bg-muted text-md md:text-sm"
            type="password"
            required
          />
        </div>

        {showTerms && (
          <p className="text-sm text-gray-600 dark:text-zinc-400">
            By signing up, you agree to our{' '}
            <Link
              href="/terms"
              className="font-semibold text-primary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              Terms of Use
            </Link>{' '}
            and{' '}
            <Link
              href="/privacy"
              className="font-semibold text-primary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            >
              Privacy Policy
            </Link>
          </p>
        )}

        {children}
      </Form>
    </div>
  );
}
