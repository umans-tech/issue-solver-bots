'use client';

import type { User } from 'next-auth';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useState, useEffect } from 'react';

import { IconUmansChat, PlusIcon } from '@/components/icons';
import { SidebarHistory } from '@/components/sidebar-history';
import { SidebarUserNav } from '@/components/sidebar-user-nav';
import { Button } from '@/components/ui/button';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  useSidebar,
} from '@/components/ui/sidebar';
import Link from 'next/link';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { SpaceSelector } from '@/components/space-selector';
import { SpaceRenameDialog } from '@/components/space-rename-dialog';
import { SpaceCreateDialog } from '@/components/space-create-dialog';

export function AppSidebar({ user }: { user: User | undefined }) {
  const router = useRouter();
  const { setOpenMobile } = useSidebar();
  const { data: session, update: updateSession } = useSession();
  const [isRenameDialogOpen, setIsRenameDialogOpen] = useState(false);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
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
    // TODO: Implement invite to space
    console.log('Invite to space');
  };

  const handleRenameSpace = () => {
    setIsRenameDialogOpen(true);
  };

  const handleSwitchSpace = async (spaceId: string) => {
    try {
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

      // Refresh the page to update the UI
      router.refresh();
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
          <div className="flex flex-row justify-between items-center">
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
        <SidebarHistory user={user} />
      </SidebarContent>
      <SidebarFooter>{user && <SidebarUserNav user={user} />}</SidebarFooter>
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
    </Sidebar>
  );
}
