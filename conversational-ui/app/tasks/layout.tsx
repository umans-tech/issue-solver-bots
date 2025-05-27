import { cookies } from 'next/headers';

import { AppSidebar } from '@/components/app-sidebar';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
import { ensureDefaultSpace } from '@/lib/db/queries';
import { Providers } from '@/components/providers';

import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/auth';
import type { Session } from 'next-auth';
import Script from 'next/script';

export const experimental_ppr = true;

export default async function TasksLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await getServerSession(authOptions) as any as Session | null;
  const cookieStore = await cookies();
  const isCollapsed = cookieStore.get('sidebar:state')?.value !== 'true';
  const theme = cookieStore.get('theme')?.value || 'system';

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
      <Providers session={session}>
        <SidebarProvider defaultOpen={!isCollapsed}>
          <AppSidebar user={session?.user} />
          <SidebarInset>{children}</SidebarInset>
        </SidebarProvider>
      </Providers>
    </>
  );
} 