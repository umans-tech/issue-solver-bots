import Link from 'next/link'
import { redirect } from 'next/navigation'
import { auth } from '@/app/(auth)/auth'

export default async function VerifyRequestPage() {
  // Redirect if already logged in
  const session = await auth()
  if (session?.user) {
    redirect('/')
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4">
      <div className="w-full max-w-md p-6 space-y-6 bg-white shadow-md rounded-lg dark:bg-gray-800">
        <div className="space-y-2 text-center">
          <h1 className="text-3xl font-bold">Check your email</h1>
          <p className="text-gray-500 dark:text-gray-400">
            A sign in link has been sent to your email address.
          </p>
        </div>
        
        <div className="space-y-4">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Please check your email inbox and click on the link to complete the sign-in process.
          </p>
          
          <p className="text-sm text-gray-500 dark:text-gray-400">
            If you don't see the email, check your spam folder.
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