import { cookies } from 'next/headers';

import { AppSidebar } from '@/components/app-sidebar';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
import { ensureDefaultSpace } from '@/lib/db/queries';
import { SessionProvider } from 'next-auth/react';

import { auth } from '../(auth)/auth';
import Script from 'next/script';

export default async function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [session, cookieStore] = await Promise.all([auth(), cookies()]);
  const isCollapsed = cookieStore.get('sidebar:state')?.value !== 'true';
  // Ensure the user has a default space if logged in
  if (session?.user?.id) {
    await ensureDefaultSpace(session.user.id);
  }

  return (
    <>
      <Script
        src="https://cdn.jsdelivr.net/pyodide/v0.23.4/full/pyodide.js"
        strategy="beforeInteractive"
      />
      <SessionProvider session={session}>
        <SidebarProvider defaultOpen={!isCollapsed}>
          <AppSidebar user={session?.user} />
          <SidebarInset>{children}</SidebarInset>
        </SidebarProvider>
      </SessionProvider>
    </>
  );
}
