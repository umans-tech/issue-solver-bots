'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

// Simple redirect to root in development
export default function GoToAppPage() {
  const router = useRouter();

  useEffect(() => {
    // In development, just go to the root
    router.replace('/');
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center">
      <p className="text-lg">Redirecting...</p>
    </div>
  );
}
