'use client';

import { useRouter } from 'next/navigation';
import { useWindowSize } from 'usehooks-ts';
import { useSession } from 'next-auth/react';
import { toast } from 'sonner';

import { Button } from '@/components/ui/button';
import { PlusIcon } from './icons';
import { Copy } from 'lucide-react';
import { useSidebar } from './ui/sidebar';
import { memo } from 'react';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';
import { VisibilitySelector, type VisibilityType } from './visibility-selector';
import { SharedHeader } from './shared-header';

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
  useSession();
  const { open } = useSidebar();

  const { width: windowWidth } = useWindowSize();
  const handleNewChat = () => {
    router.push('/');
  };

  const handleCloneConversation = async () => {
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
  };

  // Chat-specific header content (visibility selector, new chat button, clone button)
  const chatContent = (
    <>
      {/* New Chat button for mobile or when sidebar is closed */}
      {(!open || windowWidth < 768) && (
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="outline"
              className="order-2 md:order-1 md:px-2 px-2 md:h-fit ml-auto md:ml-0"
              onClick={handleNewChat}
            >
              <PlusIcon />
              <span className="md:sr-only">New Chat</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent>New Chat</TooltipContent>
        </Tooltip>
      )}

      {/* Center controls */}
      <div className="flex items-center gap-2 md:flex py-1.5 px-2 h-fit md:h-[34px] order-1 md:order-1">
        {/* Clone button for readonly conversations */}
        {isReadonly && (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="outline"
                className="order-2 md:order-1 md:px-2 px-2 md:h-fit"
                onClick={handleCloneConversation}
              >
                <Copy />
                <span className="ml-2 hidden md:inline">
                  Clone Conversation
                </span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>Clone this conversation</TooltipContent>
          </Tooltip>
        )}

        {/* Visibility selector for editable conversations */}
        {!isReadonly && (
          <VisibilitySelector
            chatId={chatId}
            selectedVisibilityType={selectedVisibilityType}
            className="order-1"
          />
        )}
      </div>
    </>
  );

  return <SharedHeader enableSessionRefresh={true}>{chatContent}</SharedHeader>;
}

export const ChatHeader = memo(PureChatHeader, (prevProps, nextProps) => {
  // Always re-render when status might have changed
  return false;
});
