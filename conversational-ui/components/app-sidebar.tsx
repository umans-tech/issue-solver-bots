'use client';

import type { User } from 'next-auth';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useState, useEffect } from 'react';
import { CheckSquare, Plug, MessageCircle } from 'lucide-react';
import Link from 'next/link';

import { PlusIcon } from '@/components/icons';
import { SidebarHistory } from '@/components/sidebar-history';
import { SidebarUserNav } from '@/components/sidebar-user-nav';
import { Button } from '@/components/ui/button';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarGroup,
  SidebarGroupContent,
  useSidebar,
} from '@/components/ui/sidebar';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { SpaceSelector } from '@/components/space-selector';
import { SpaceRenameDialog } from '@/components/space-rename-dialog';
import { SpaceCreateDialog } from '@/components/space-create-dialog';
import { SpaceInviteDialog } from '@/components/space-invite-dialog';

export function AppSidebar({ user }: { user: User | undefined }) {
  const router = useRouter();
  const { setOpenMobile } = useSidebar();
  const { data: session, update: updateSession } = useSession();
  const [isRenameDialogOpen, setIsRenameDialogOpen] = useState(false);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isInviteDialogOpen, setIsInviteDialogOpen] = useState(false);
  const [spaces, setSpaces] = useState<any[]>([]);

  const fetchSpaces = async () => {
    if (!session?.user?.id) return;
    
    try {
      console.log('Fetching spaces...');
      const response = await fetch('/api/spaces/list');
      if (!response.ok) {
        throw new Error('Failed to fetch spaces');
      }
      const fetchedSpaces = await response.json();
      console.log('Fetched spaces:', fetchedSpaces);
      
      setSpaces(fetchedSpaces);
      
      // Update session with spaces
      await updateSession({
        ...session,
        user: {
          ...session.user,
          spaces: fetchedSpaces,
        },
      });
    } catch (error) {
      console.error('Error fetching spaces:', error);
    }
  };

  // Charger la liste des spaces au chargement initial et quand la session change
  useEffect(() => {
    if (session?.user?.id) {
      console.log('Session changed, fetching spaces...');
      fetchSpaces();
    }
  }, [session?.user?.id]);

  const handleCreateSpace = () => {
    setIsCreateDialogOpen(true);
  };

  const handleInviteToSpace = () => {
    setIsInviteDialogOpen(true);
  };

  const handleRenameSpace = () => {
    setIsRenameDialogOpen(true);
  };

  const handleSwitchSpace = async (spaceId: string) => {
    try {
      // Check if we're currently in a chat
      const currentPath = window.location.pathname;
      const chatMatch = currentPath.match(/^\/chat\/([^\/]+)$/);
      const currentChatId = chatMatch ? chatMatch[1] : null;

      // If we're in a chat, check if it belongs to the new space
      let shouldRedirectToHome = false;
      if (currentChatId) {
        try {
          const chatResponse = await fetch(`/api/chat/check-space`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chatId: currentChatId, spaceId }),
          });

          if (chatResponse.ok) {
            const { belongsToSpace } = await chatResponse.json();
            shouldRedirectToHome = !belongsToSpace;
          }
        } catch (error) {
          console.error('Error checking chat space:', error);
          // If we can't check, err on the side of caution and redirect
          shouldRedirectToHome = true;
        }
      }

      const response = await fetch('/api/spaces/switch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ spaceId }),
      });

      if (!response.ok) {
        throw new Error('Failed to switch space');
      }

      const newSpace = await response.json();
      
      // Find the space in our local state
      const selectedSpace = spaces.find(space => space.id === spaceId);

      // Update the session with the new selected space and all spaces
      await updateSession({
        ...session,
        user: {
          ...session?.user,
          selectedSpace: selectedSpace,
          spaces: spaces,
        },
      });

      // Navigate based on whether the current chat belongs to the new space
      if (shouldRedirectToHome) {
        router.push('/');
      }
    } catch (error) {
      console.error('Error switching space:', error);
    }
  };

  const handleCreateSuccess = async () => {
    // Recharger la liste des spaces après la création
    console.log('Space created, refreshing list...');
    await fetchSpaces();
  };

  console.log('Current session:', session);
  console.log('Current spaces:', spaces);

  return (
    <Sidebar className="group-data-[side=left]:border-r-0">
      <SidebarHeader>
        <SidebarMenu>
          <div className="flex w-full flex-row justify-between items-center">
            <SpaceSelector 
              spaceName={session?.user?.selectedSpace?.name || 'Chatbot'}
              spaceId={session?.user?.selectedSpace?.id || ''}
              spaces={spaces}
              onCreateSpace={handleCreateSpace}
              onInviteToSpace={handleInviteToSpace}
              onRenameSpace={handleRenameSpace}
              onSwitchSpace={handleSwitchSpace}
            />
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  type="button"
                  className="p-2 h-fit"
                  onClick={() => {
                    setOpenMobile(false);
                    router.push('/');
                    router.refresh();
                  }}
                >
                  <PlusIcon />
                </Button>
              </TooltipTrigger>
              <TooltipContent align="end">New Chat</TooltipContent>
            </Tooltip>
          </div>
        </SidebarMenu>
      </SidebarHeader>
      
      <SidebarContent>
        {/* Conversations Section */}
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
            <SidebarHistory user={user} />
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      
      <SidebarFooter>
        {/* Tasks Section */}
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                  <Link href="/tasks" className="w-full flex items-center gap-2">
                    <CheckSquare className="h-4 w-4" />
                    <span>Tasks</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        
        {/* Integrations Section */}
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                  <button className="w-full flex items-center gap-2">
                    <Plug className="h-4 w-4" />
                    <span>Integrations</span>
                  </button>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        
        {user && <SidebarUserNav user={user} />}
      </SidebarFooter>
      <SpaceRenameDialog
        open={isRenameDialogOpen}
        onOpenChange={setIsRenameDialogOpen}
        currentName={session?.user?.selectedSpace?.name || ''}
        spaceId={session?.user?.selectedSpace?.id || ''}
      />
      <SpaceCreateDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
        onSuccess={handleCreateSuccess}
      />
      <SpaceInviteDialog
        open={isInviteDialogOpen}
        onOpenChange={setIsInviteDialogOpen}
        spaceId={session?.user?.selectedSpace?.id || ''}
        spaceName={session?.user?.selectedSpace?.name || ''}
      />
    </Sidebar>
  );
}
