'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useWindowSize } from 'usehooks-ts';
import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { toast } from 'sonner';

import { SidebarToggle } from '@/components/sidebar-toggle';
import { Button } from '@/components/ui/button';
import { PlusIcon, GitIcon, CopyIcon } from './icons';
import { useSidebar } from './ui/sidebar';
import { memo } from 'react';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';
import { VisibilityType, VisibilitySelector } from './visibility-selector';
import { ThemeToggle } from './theme-toggle';
import { IconUmansLogo } from './icons';
import { RepoConnectionDialog } from './repo-connection-dialog/repo-connection-dialog';
import { useProcessStatus } from '@/hooks/use-process-status';

function PureChatHeader({
  chatId,
  selectedVisibilityType,
  isReadonly,
}: {
  chatId: string;
  selectedVisibilityType: VisibilityType;
  isReadonly: boolean;
}) {
  const router = useRouter();
  const { data: session, update: updateSession } = useSession();
  const { open } = useSidebar();
  const [showRepoDialog, setShowRepoDialog] = useState(false);
  const [isSessionRefreshed, setIsSessionRefreshed] = useState(false);

  const { width: windowWidth } = useWindowSize();

  // Refresh session on component mount to ensure latest space data
  useEffect(() => {
    const refreshSession = async () => {
      if (isSessionRefreshed) return; // Prevent multiple refreshes
      
      try {
        console.log("Attempting to refresh session from server...");
        
        // Call our custom session refresh endpoint
        const response = await fetch('/api/auth/session', { 
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
          }
        });
        
        if (response.ok) {
          const freshSession = await response.json();
          console.log("Refreshed session data on mount:", {
            knowledgeBaseId: freshSession?.user?.selectedSpace?.knowledgeBaseId,
            processId: freshSession?.user?.selectedSpace?.processId
          });
          
          // Update session with fresh data
          await updateSession(freshSession);
          console.log("Chat header session refreshed on mount");
          setIsSessionRefreshed(true);
        } else {
          console.error("Failed to refresh session:", response.statusText);
        }
      } catch (error) {
        console.error("Error refreshing session on mount:", error);
      }
    };
    
    refreshSession();
  }, [updateSession, isSessionRefreshed]);

  // Get repository data from session
  const knowledgeBaseId = session?.user?.selectedSpace?.knowledgeBaseId;
  const processId = session?.user?.selectedSpace?.processId;
  
  // Log all relevant session data for debugging
  useEffect(() => {
    console.log("Session data in ChatHeader:", {
      knowledgeBaseId,
      processId,
      selectedSpaceId: session?.user?.selectedSpace?.id,
      hasSession: !!session,
      hasUser: !!session?.user,
      hasSelectedSpace: !!session?.user?.selectedSpace
    });
  }, [session, knowledgeBaseId, processId]);

  // Define initial status based on session data
  let initialStatus: 'none' | 'indexing' | 'indexed' = 'none';
  
  // If there's a knowledgeBaseId but no processId, it's already indexed
  if (knowledgeBaseId && !processId) {
    initialStatus = 'indexed';
  }
  
  // Use our custom hook to poll the process status
  const gitStatus = useProcessStatus(processId, initialStatus);
  
  // Log status for debugging
  useEffect(() => {
    console.log(`Git status in ChatHeader: ${gitStatus}, KB: ${knowledgeBaseId}, Process: ${processId}`);
  }, [gitStatus, knowledgeBaseId, processId]);

  return (
    <header className="sticky top-0 z-50 flex items-center justify-between w-full h-16 px-4 border-b shrink-0 bg-background">
      <div className="flex items-center">
        <SidebarToggle />
      </div>

      {(!open || windowWidth < 768) && (
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="outline"
              className="order-2 md:order-1 md:px-2 px-2 md:h-fit ml-auto md:ml-0"
              onClick={() => {
                router.push('/');
                router.refresh();
              }}
            >
              <PlusIcon />
              <span className="md:sr-only">New Chat</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent>New Chat</TooltipContent>
        </Tooltip>
      )}

      <div className="flex items-center gap-2 md:flex py-1.5 px-2 h-fit md:h-[34px] order-1 md:order-1">
        {isReadonly && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="order-2 md:order-1 md:px-2 px-2 md:h-fit"
                onClick={async () => {
                  try {
                    const response = await fetch('/api/clone', {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                      },
                      body: JSON.stringify({
                        sourceChatId: chatId,
                      }),
                    });
                    
                    if (!response.ok) {
                      throw new Error('Failed to clone conversation');
                    }
                    
                    const data = await response.json();
                    if (data.success && data.newChatId) {
                      toast.success('Created a clone of this conversation!');
                      // Navigate to the new chat
                      router.push(`/chat/${data.newChatId}`);
                    }
                  } catch (error) {
                    console.error('Error cloning conversation:', error);
                    toast.error('Failed to clone conversation');
                  }
                }}
              >
                <CopyIcon />
                <span className="ml-2 hidden md:inline">Clone Conversation</span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>Clone this conversation</TooltipContent>
          </Tooltip>
        )}
        {!isReadonly && (
          <VisibilitySelector
            chatId={chatId}
            selectedVisibilityType={selectedVisibilityType}
            className="order-1"
          />
        )}
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

      <RepoConnectionDialog 
        open={showRepoDialog} 
        onOpenChange={setShowRepoDialog} 
      />
    </header>
  );
}

export const ChatHeader = memo(PureChatHeader, (prevProps, nextProps) => {
  // Always re-render when status might have changed
  return false;
});
