'use client';

import type { User } from 'next-auth';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useState } from 'react';

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

      // Update the session with the new space data
      await updateSession({
        user: {
          ...session?.user,
          selectedSpace: newSpace,
        },
      });

      // Refresh the page to update the UI
      router.refresh();
    } catch (error) {
      console.error('Error switching space:', error);
    }
  };

  return (
    <Sidebar className="group-data-[side=left]:border-r-0">
      <SidebarHeader>
        <SidebarMenu>
          <div className="flex flex-row justify-between items-center">
            <SpaceSelector 
              spaceName={session?.user?.selectedSpace?.name || 'Chatbot'}
              spaceId={session?.user?.selectedSpace?.id || ''}
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
      />
    </Sidebar>
  );
}
