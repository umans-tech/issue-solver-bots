'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useSession } from 'next-auth/react';
import { SidebarToggle } from '@/components/sidebar-toggle';
import { Button } from '@/components/ui/button';
import { GitIcon, IconUmansLogo } from './icons';
import { ThemeToggle } from './theme-toggle';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';
import { RepoConnectionDialog } from './repo-connection-dialog';
import { useProcessStatus } from '@/hooks/use-process-status';

interface SharedHeaderProps {
  enableSessionRefresh?: boolean;
  children?: React.ReactNode; // For additional header content (like visibility selector in chat)
  rightExtra?: React.ReactNode; // Allows pages to inject ephemeral right area content (e.g., status badge)
}

export function SharedHeader({
  enableSessionRefresh = false,
  children,
  rightExtra,
}: SharedHeaderProps) {
  const { data: session, update: updateSession } = useSession();
  const [showRepoDialog, setShowRepoDialog] = useState(false);
  const [isSessionRefreshed, setIsSessionRefreshed] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const handleOpen = () => setShowRepoDialog(true);
    const listener = (_event: Event) => handleOpen();
    window.addEventListener('open-repo-dialog', listener);
    return () => window.removeEventListener('open-repo-dialog', listener);
  }, []);

  // Session refresh logic - only enabled for chat where it's needed
  useEffect(() => {
    if (!enableSessionRefresh) return;

    const refreshSession = async () => {
      if (isSessionRefreshed) return; // Prevent multiple refreshes

      // Only try to refresh session if user is authenticated
      if (!session?.user) {
        console.log('No authenticated user, skipping session refresh');
        return;
      }

      try {
        console.log('Attempting to refresh session from server...');

        // Call our custom session refresh endpoint
        const response = await fetch('/api/auth/session', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
          },
        });

        if (response.ok) {
          const freshSession = await response.json();
          console.log('Refreshed session data on mount:', {
            knowledgeBaseId: freshSession?.user?.selectedSpace?.knowledgeBaseId,
            processId: freshSession?.user?.selectedSpace?.processId,
          });

          // Update session with fresh data
          await updateSession(freshSession);
          console.log('Session refreshed on mount');
          setIsSessionRefreshed(true);
        } else {
          console.log(
            'Session refresh failed:',
            response.status,
            response.statusText,
          );
        }
      } catch (error) {
        console.error('Error refreshing session on mount:', error);
      }
    };

    refreshSession();
  }, [updateSession, isSessionRefreshed, session?.user, enableSessionRefresh]);

  // Get repository data from session for the git status
  const processId = session?.user?.selectedSpace?.processId;
  const knowledgeBaseId = session?.user?.selectedSpace?.knowledgeBaseId;

  // Log all relevant session data for debugging in development
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log('Session data in SharedHeader:', {
        knowledgeBaseId,
        processId,
        selectedSpaceId: session?.user?.selectedSpace?.id,
        hasSession: !!session,
        hasUser: !!session?.user,
        hasSelectedSpace: !!session?.user?.selectedSpace,
      });
    }
  }, [session, knowledgeBaseId, processId]);

  // Use our custom hook to poll the process status (now determines initial status internally)
  const gitStatus = useProcessStatus(processId);

  // Log status for debugging in development
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      console.log(
        `Git status: ${gitStatus}, KB: ${knowledgeBaseId}, Process: ${processId}`,
      );
    }
  }, [gitStatus, knowledgeBaseId, processId]);

  return (
    <>
      <header className="sticky top-0 z-50 flex items-center justify-between w-full h-16 px-4 border-b shrink-0 bg-background">
        <div className="flex items-center">
          <SidebarToggle />
        </div>

        {/* Additional header content (like visibility selector for chat) */}
        {children}

        {/* Expandable center area (rightExtra) separated from icons */}
        <div className="hidden md:flex shrink-0 items-center justify-end px-3 border-r">
          {rightExtra}
        </div>

        <div className="flex items-center gap-2 md:flex py-1.5 px-2 h-fit md:h-[34px] order-4 md:ml-auto">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className="h-8 w-8"
                onClick={() => setShowRepoDialog(true)}
              >
                <GitIcon status={gitStatus} />
                <span className="sr-only">Connect Repository</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              {gitStatus === 'none' && 'Connect Repository'}
              {gitStatus === 'indexing' && 'Repository Indexing - In Progress'}
              {gitStatus === 'indexed' && 'Repository Indexing - Completed'}
            </TooltipContent>
          </Tooltip>
          <ThemeToggle />
          <Link href="/landing">
            <IconUmansLogo className="h-16 w-16" />
          </Link>
        </div>
      </header>

      <RepoConnectionDialog
        key={session?.user?.selectedSpace?.id}
        open={showRepoDialog}
        onOpenChange={setShowRepoDialog}
      />
    </>
  );
}
