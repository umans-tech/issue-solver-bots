import Link from 'next/link'
import { redirect } from 'next/navigation'
import { auth } from '@/app/(auth)/auth'

export default async function AuthErrorPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string }>
}) {
  // Redirect if already logged in
  const session = await auth()
  if (session?.user) {
    redirect('/')
  }

  const params = await searchParams
  const error = params.error || 'default'
  
  // Map error codes to user-friendly messages
  const errorMessages: Record<string, string> = {
    default: 'An error occurred during authentication.',
    configuration: 'There is a problem with the server configuration.',
    accessdenied: 'You do not have permission to sign in.',
    verification: 'The verification link has expired or has already been used.',
    signin: 'Try signing in with a different account.',
    oauthsignin: 'Error in the OAuth sign-in process.',
    oauthcallback: 'Error in the OAuth callback process.',
    oauthcreateaccount: 'Could not create OAuth provider account.',
    emailcreateaccount: 'Could not create email provider account.',
    callback: 'Error in the authentication callback.',
    credentials: 'Invalid credentials.',
    emailsignin: 'Error sending the email with sign-in link.',
    session: 'Error in retrieving session.',
  }

  const errorMessage = errorMessages[error] || errorMessages.default

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <div className="w-full max-w-md p-6 space-y-6 bg-white shadow-md rounded-lg dark:bg-gray-800">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-bold text-red-600 dark:text-red-400">Authentication Error</h1>
          <p className="text-gray-500 dark:text-gray-400">
            {errorMessage}
          </p>
        </div>
        
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <Link 
            href="/login"
            className="w-full inline-flex justify-center text-sm font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
          >
            Return to login
          </Link>
        </div>
      </div>
    </div>
  )
}