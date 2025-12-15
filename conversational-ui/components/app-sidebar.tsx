'use client';

import type { User } from 'next-auth';
import { useRouter } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { useEffect, useState } from 'react';
import { Activity, BookText, Plug } from 'lucide-react';
import Link from 'next/link';

import { PlusIcon } from '@/components/icons';
import { SidebarHistory } from '@/components/sidebar-history';
import { SidebarUserNav } from '@/components/sidebar-user-nav';
import { Button } from '@/components/ui/button';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { SpaceSelector } from '@/components/space-selector';
import { SpaceRenameDialog } from '@/components/space-rename-dialog';
import { SpaceCreateDialog } from '@/components/space-create-dialog';
import { SpaceInviteDialog } from '@/components/space-invite-dialog';
import { SpaceMembersDialog } from '@/components/space-members-dialog';

type SpaceSummary = {
  id: string;
  name: string;
  knowledgeBaseId?: string | null;
  processId?: string | null;
  connectedRepoUrl?: string | null;
  isDefault?: boolean;
};

const toSpaceSummary = (maybeSpace: any): SpaceSummary | null => {
  if (!maybeSpace?.id || !maybeSpace?.name) {
    return null;
  }

  return {
    id: maybeSpace.id,
    name: maybeSpace.name,
    knowledgeBaseId: maybeSpace.knowledgeBaseId ?? null,
    processId: maybeSpace.processId ?? null,
    connectedRepoUrl: maybeSpace.connectedRepoUrl ?? null,
    isDefault: maybeSpace.isDefault ?? false,
  };
};

export function AppSidebar({ user }: { user: User | undefined }) {
  const router = useRouter();
  const { setOpenMobile } = useSidebar();
  const { data: session, update: updateSession } = useSession();
  const [isRenameDialogOpen, setIsRenameDialogOpen] = useState(false);
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isInviteDialogOpen, setIsInviteDialogOpen] = useState(false);
  const [isMembersDialogOpen, setIsMembersDialogOpen] = useState(false);

  const [spaces, setSpaces] = useState<SpaceSummary[]>([]);
  const [activeSpace, setActiveSpace] = useState<SpaceSummary | null>(
    toSpaceSummary(session?.user?.selectedSpace ?? user?.selectedSpace ?? null),
  );

  const fetchSpaces = async (): Promise<SpaceSummary[] | undefined> => {
    if (!session?.user?.id) return;

    try {
      const response = await fetch('/api/spaces/list');
      if (!response.ok) {
        throw new Error('Failed to fetch spaces');
      }
      const fetchedSpaces: SpaceSummary[] = await response.json();

      setSpaces(fetchedSpaces);

      // Update session with spaces
      await updateSession({
        ...session,
        user: {
          ...session.user,
          spaces: fetchedSpaces,
        },
      });

      return fetchedSpaces;
    } catch (error) {
      console.error('Error fetching spaces:', error);
      return;
    }
  };

  // Charger la liste des spaces au chargement initial et quand la session change
  useEffect(() => {
    if (session?.user?.id) {
      fetchSpaces();
    }
  }, [session?.user?.id]);

  useEffect(() => {
    const sessionSpace = toSpaceSummary(session?.user?.selectedSpace ?? null);
    if (sessionSpace) {
      setActiveSpace((previous) => {
        if (!previous || previous.id !== sessionSpace.id) {
          return sessionSpace;
        }

        if (previous.name !== sessionSpace.name) {
          return { ...previous, name: sessionSpace.name };
        }

        return previous;
      });
    }
  }, [session?.user?.selectedSpace?.id, session?.user?.selectedSpace?.name]);

  useEffect(() => {
    if (!spaces.length) return;

    setActiveSpace((previous) => {
      if (previous) {
        const matchingSpace = spaces.find((space) => space.id === previous.id);
        return matchingSpace ?? previous;
      }

      const fallbackSpace =
        spaces.find((space) => space.isDefault) ?? spaces[0];
      return fallbackSpace ?? null;
    });
  }, [spaces]);

  const handleCreateSpace = () => {
    setIsCreateDialogOpen(true);
  };

  const handleInviteToSpace = () => {
    setIsInviteDialogOpen(true);
  };

  const handleViewMembers = () => {
    setIsMembersDialogOpen(true);
  };

  const handleRenameSpace = () => {
    setIsRenameDialogOpen(true);
  };

  const switchToSpace = async (
    spaceId: string,
    skipSpaceListRefresh = false,
  ) => {
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

      const switchedSpace = toSpaceSummary(await response.json());

      let latestSpaces = spaces;
      if (!skipSpaceListRefresh) {
        const refreshedSpaces = await fetchSpaces();
        if (refreshedSpaces) {
          latestSpaces = refreshedSpaces;
        }
      }

      // Find the space in our local state
      let selectedSpace = latestSpaces.find((space) => space.id === spaceId);
      if (!selectedSpace && switchedSpace) {
        selectedSpace = switchedSpace;
        if (!latestSpaces.some((space) => space.id === switchedSpace.id)) {
          latestSpaces = [...latestSpaces, switchedSpace];
          setSpaces(latestSpaces);
        }
      }

      // Update the session with the new selected space and all spaces
      await updateSession({
        ...session,
        user: {
          ...session?.user,
          selectedSpace: selectedSpace,
          spaces: latestSpaces,
        },
      });

      if (selectedSpace) {
        setActiveSpace(selectedSpace);
      }

      // Navigate based on whether the current chat belongs to the new space
      if (shouldRedirectToHome) {
        router.push('/');
      }
    } catch (error) {
      console.error('Error switching to space:', error);
      throw error;
    }
  };

  const handleSwitchSpace = async (spaceId: string) => {
    await switchToSpace(spaceId);
  };

  const handleCreateSuccess = async (newSpaceId: string) => {
    await fetchSpaces();
    await switchToSpace(newSpaceId, true);
  };

  return (
    <Sidebar className="group-data-[side=left]:border-r-0">
      <SidebarHeader>
        <SidebarMenu>
          <div className="flex w-full flex-row justify-between items-center">
            <SpaceSelector
              spaceName={activeSpace?.name || 'Loading space...'}
              spaceId={activeSpace?.id || ''}
              spaces={spaces}
              onCreateSpace={handleCreateSpace}
              onInviteToSpace={handleInviteToSpace}
              onViewMembers={handleViewMembers}
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
                <SidebarMenuButton asChild />
              </SidebarMenuItem>
            </SidebarMenu>
            <SidebarHistory user={user} />
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        {/* Docs Section */}
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                  <Link href="/docs" className="w-full flex items-center gap-2">
                    <BookText className="h-4 w-4" />
                    <span>Docs</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        {/* Tasks Section */}
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton asChild>
                  <Link
                    href="/tasks"
                    className="w-full flex items-center gap-2"
                  >
                    <Activity className="h-4 w-4" />
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
                  <Link
                    href="/integrations"
                    className="w-full flex items-center gap-2"
                  >
                    <Plug className="h-4 w-4" />
                    <span>Integrations</span>
                  </Link>
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
        currentName={activeSpace?.name || ''}
        spaceId={activeSpace?.id || ''}
      />
      <SpaceCreateDialog
        open={isCreateDialogOpen}
        onOpenChange={setIsCreateDialogOpen}
        onSuccess={handleCreateSuccess}
      />
      <SpaceInviteDialog
        open={isInviteDialogOpen}
        onOpenChange={setIsInviteDialogOpen}
        spaceId={activeSpace?.id || ''}
        spaceName={activeSpace?.name || ''}
      />
      <SpaceMembersDialog
        open={isMembersDialogOpen}
        onOpenChange={setIsMembersDialogOpen}
        spaceId={activeSpace?.id || ''}
        spaceName={activeSpace?.name || ''}
      />
    </Sidebar>
  );
}
