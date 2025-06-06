'use client';

import { isToday, isYesterday, subMonths, subWeeks } from 'date-fns';
import Link from 'next/link';
import { useParams, usePathname, useRouter } from 'next/navigation';
import type { User } from 'next-auth';
import { memo, useEffect, useState } from 'react';
import { toast } from 'sonner';
import useSWR from 'swr';
import { useSession } from 'next-auth/react';

import {
  CheckCircleFillIcon,
  GlobeIcon,
  LockIcon,
  MoreHorizontalIcon,
  PencilEditIcon,
  ShareIcon,
  TrashIcon,
} from '@/components/icons';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuSub,
  DropdownMenuSubContent,
  DropdownMenuSubTrigger,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  SidebarMenu,
  SidebarMenuAction,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from '@/components/ui/sidebar';
import type { Chat } from '@/lib/db/schema';
import { fetcher } from '@/lib/utils';
import { useChatVisibility } from '@/hooks/use-chat-visibility';
import { ChatRenameDialog } from './chat-rename-dialog';

type GroupedChats = {
  today: Chat[];
  yesterday: Chat[];
  lastWeek: Chat[];
  lastMonth: Chat[];
  older: Chat[];
};

const PureChatItem = ({
  chat,
  isActive,
  onDelete,
  setOpenMobile,
  mutate,
}: {
  chat: Chat;
  isActive: boolean;
  onDelete: (chatId: string) => void;
  setOpenMobile: (open: boolean) => void;
  mutate: (...args: any[]) => any;
}) => {
  const { visibilityType, setVisibilityType } = useChatVisibility({
    chatId: chat.id,
    initialVisibility: chat.visibility,
  });
  const [showRenameDialog, setShowRenameDialog] = useState(false);
  const [localTitle, setLocalTitle] = useState(chat.title);

  useEffect(() => {
    setLocalTitle(chat.title);
  }, [chat.title]);

  return (
    <SidebarMenuItem>
      <SidebarMenuButton asChild isActive={isActive}>
        <Link href={`/chat/${chat.id}`} onClick={() => setOpenMobile(false)}>
          <span>{localTitle}</span>
        </Link>
      </SidebarMenuButton>

      <DropdownMenu modal={true}>
        <DropdownMenuTrigger asChild>
          <SidebarMenuAction
            className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground mr-0.5"
            showOnHover={!isActive}
          >
            <MoreHorizontalIcon />
            <span className="sr-only">More</span>
          </SidebarMenuAction>
        </DropdownMenuTrigger>

        <DropdownMenuContent side="bottom" align="end">
          <DropdownMenuItem
            className="cursor-pointer"
            onClick={() => setShowRenameDialog(true)}
          >
            <PencilEditIcon />
            <span>Rename</span>
          </DropdownMenuItem>

          <DropdownMenuSub>
            <DropdownMenuSubTrigger className="cursor-pointer">
              <ShareIcon />
              <span>Share</span>
            </DropdownMenuSubTrigger>
            <DropdownMenuPortal>
              <DropdownMenuSubContent>
                <DropdownMenuItem
                  className="cursor-pointer flex-row justify-between"
                  onClick={() => {
                    setVisibilityType('private');
                  }}
                >
                  <div className="flex flex-row gap-2 items-center">
                    <LockIcon size={12} />
                    <span>Private</span>
                  </div>
                  {visibilityType === 'private' ? (
                    <CheckCircleFillIcon />
                  ) : null}
                </DropdownMenuItem>
                <DropdownMenuItem
                  className="cursor-pointer flex-row justify-between"
                  onClick={() => {
                    setVisibilityType('public');
                  }}
                >
                  <div className="flex flex-row gap-2 items-center">
                    <GlobeIcon />
                    <span>Public</span>
                  </div>
                  {visibilityType === 'public' ? <CheckCircleFillIcon /> : null}
                </DropdownMenuItem>
              </DropdownMenuSubContent>
            </DropdownMenuPortal>
          </DropdownMenuSub>

          <DropdownMenuItem
            className="cursor-pointer text-destructive focus:bg-destructive/15 focus:text-destructive dark:text-red-500"
            onSelect={() => onDelete(chat.id)}
          >
            <TrashIcon />
            <span>Delete</span>
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <ChatRenameDialog
        open={showRenameDialog}
        onOpenChange={setShowRenameDialog}
        chatId={chat.id}
        currentTitle={localTitle}
        onSuccess={(newTitle: string) => {
          setLocalTitle(newTitle);
          mutate();
        }}
      />
    </SidebarMenuItem>
  );
};

export const ChatItem = memo(PureChatItem, (prevProps, nextProps) => {
  if (
    prevProps.isActive !== nextProps.isActive ||
    prevProps.chat.title !== nextProps.chat.title
  ) {
    return false;
  }
  return true;
});

export function SidebarHistory({ user }: { user: User | undefined }) {
  const { setOpenMobile } = useSidebar();
  const { data: session } = useSession();
  const params = useParams();
  const id = typeof params?.id === 'string' ? params.id : undefined;
  const pathname = usePathname();
  const {
    data: history,
    isLoading,
    mutate: refreshHistory,
  } = useSWR<Array<Chat>>(user ? '/api/history' : null, fetcher, {
    fallbackData: [],
  });

  useEffect(() => {
    refreshHistory();
  }, [
    pathname, 
    refreshHistory, 
    session?.user?.selectedSpace?.id
  ]);

  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const router = useRouter();
  const handleDelete = async () => {
    const deletePromise = fetch(`/api/chat?id=${deleteId}`, {
      method: 'DELETE',
    });

    toast.promise(deletePromise, {
      loading: 'Deleting chat...',
      success: () => {
        refreshHistory((history) => {
          if (history) {
            return history.filter((h) => h.id !== id);
          }
        });
        return 'Chat deleted successfully';
      },
      error: 'Failed to delete chat',
    });

    setShowDeleteDialog(false);

    if (deleteId === id) {
      router.push('/');
    }
  };

  if (!user) {
    return (
      <div className="px-2 text-zinc-500 w-full flex flex-row justify-center items-center text-sm gap-2">
        Login to save and revisit previous chats!
      </div>
    );
  }

  if (isLoading) {
    return (
      <>
        <div className="px-2 py-1 text-xs text-sidebar-foreground/50">
          Today
        </div>
        <div className="flex flex-col">
          {[44, 32, 28, 64, 52].map((item) => (
            <div
              key={item}
              className="rounded-md h-8 flex gap-2 px-2 items-center"
            >
              <div
                className="h-4 rounded-md flex-1 max-w-[--skeleton-width] bg-sidebar-accent-foreground/10"
                style={
                  {
                    '--skeleton-width': `${item}%`,
                  } as React.CSSProperties
                }
              />
            </div>
          ))}
        </div>
      </>
    );
  }

  if (history?.length === 0) {
    return (
      <div className="px-2 text-zinc-500 w-full flex flex-row justify-center items-center text-sm gap-2">
        Your conversations will appear here once you start chatting!
      </div>
    );
  }

  const groupChatsByDate = (chats: Chat[]): GroupedChats => {
    const now = new Date();
    const oneWeekAgo = subWeeks(now, 1);
    const oneMonthAgo = subMonths(now, 1);

    return chats.reduce(
      (groups, chat) => {
        const chatDate = new Date(chat.createdAt);

        if (isToday(chatDate)) {
          groups.today.push(chat);
        } else if (isYesterday(chatDate)) {
          groups.yesterday.push(chat);
        } else if (chatDate > oneWeekAgo) {
          groups.lastWeek.push(chat);
        } else if (chatDate > oneMonthAgo) {
          groups.lastMonth.push(chat);
        } else {
          groups.older.push(chat);
        }

        return groups;
      },
      {
        today: [],
        yesterday: [],
        lastWeek: [],
        lastMonth: [],
        older: [],
      } as GroupedChats,
    );
  };

  return (
    <>
      <SidebarMenu>
        {history &&
          (() => {
            const groupedChats = groupChatsByDate(history);

            return (
              <>
                {groupedChats.today.length > 0 && (
                  <>
                    <div className="px-2 py-1 text-xs text-sidebar-foreground/50">
                      Today
                    </div>
                    {groupedChats.today.map((chat) => (
                      <ChatItem
                        key={chat.id}
                        chat={chat}
                        isActive={chat.id === id}
                        onDelete={(chatId) => {
                          setDeleteId(chatId);
                          setShowDeleteDialog(true);
                        }}
                        setOpenMobile={setOpenMobile}
                        mutate={refreshHistory}
                      />
                    ))}
                  </>
                )}

                {groupedChats.yesterday.length > 0 && (
                  <>
                    <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                      Yesterday
                    </div>
                    {groupedChats.yesterday.map((chat) => (
                      <ChatItem
                        key={chat.id}
                        chat={chat}
                        isActive={chat.id === id}
                        onDelete={(chatId) => {
                          setDeleteId(chatId);
                          setShowDeleteDialog(true);
                        }}
                        setOpenMobile={setOpenMobile}
                        mutate={refreshHistory}
                      />
                    ))}
                  </>
                )}

                {groupedChats.lastWeek.length > 0 && (
                  <>
                    <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                      Last 7 days
                    </div>
                    {groupedChats.lastWeek.map((chat) => (
                      <ChatItem
                        key={chat.id}
                        chat={chat}
                        isActive={chat.id === id}
                        onDelete={(chatId) => {
                          setDeleteId(chatId);
                          setShowDeleteDialog(true);
                        }}
                        setOpenMobile={setOpenMobile}
                        mutate={refreshHistory}
                      />
                    ))}
                  </>
                )}

                {groupedChats.lastMonth.length > 0 && (
                  <>
                    <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                      Last 30 days
                    </div>
                    {groupedChats.lastMonth.map((chat) => (
                      <ChatItem
                        key={chat.id}
                        chat={chat}
                        isActive={chat.id === id}
                        onDelete={(chatId) => {
                          setDeleteId(chatId);
                          setShowDeleteDialog(true);
                        }}
                        setOpenMobile={setOpenMobile}
                        mutate={refreshHistory}
                      />
                    ))}
                  </>
                )}

                {groupedChats.older.length > 0 && (
                  <>
                    <div className="px-2 py-1 text-xs text-sidebar-foreground/50 mt-6">
                      Older
                    </div>
                    {groupedChats.older.map((chat) => (
                      <ChatItem
                        key={chat.id}
                        chat={chat}
                        isActive={chat.id === id}
                        onDelete={(chatId) => {
                          setDeleteId(chatId);
                          setShowDeleteDialog(true);
                        }}
                        setOpenMobile={setOpenMobile}
                        mutate={refreshHistory}
                      />
                    ))}
                  </>
                )}
              </>
            );
          })()}
      </SidebarMenu>
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. This will permanently delete your
              chat and remove it from our servers.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete}>
              Continue
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
