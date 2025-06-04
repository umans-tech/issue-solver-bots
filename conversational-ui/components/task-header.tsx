'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { useSession } from 'next-auth/react';
import { SidebarToggle } from '@/components/sidebar-toggle';
import { Button } from '@/components/ui/button';
import { GitIcon } from './icons';
import { useSidebar } from './ui/sidebar';
import { ThemeToggle } from './theme-toggle';
import { IconUmansLogo } from './icons';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';
import { RepoConnectionDialog } from './repo-connection-dialog';
import { useProcessStatus } from '@/hooks/use-process-status';

export function TaskHeader() {
  const router = useRouter();
  const { data: session } = useSession();
  const [showRepoDialog, setShowRepoDialog] = useState(false);

  // Get repository data from session for the git status
  const processId = session?.user?.selectedSpace?.processId;
  const knowledgeBaseId = session?.user?.selectedSpace?.knowledgeBaseId;
  
  // Define initial status based on session data
  let initialStatus: 'none' | 'indexing' | 'indexed' = 'none';
  if (knowledgeBaseId && !processId) {
    initialStatus = 'indexed';
  }
  
  // Use our custom hook to poll the process status
  const gitStatus = useProcessStatus(processId, initialStatus);

  return (
    <>
      <header className="sticky top-0 z-50 flex items-center justify-between w-full h-16 px-4 border-b shrink-0 bg-background">
        <div className="flex items-center">
          <SidebarToggle />
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
        open={showRepoDialog} 
        onOpenChange={setShowRepoDialog} 
      />
    </>
  );
} 