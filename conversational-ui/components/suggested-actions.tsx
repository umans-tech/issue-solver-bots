'use client';

import { motion } from 'framer-motion';
import { Button } from './ui/button';
import { memo, useState } from 'react';
import { useSession } from 'next-auth/react';
import { RepoConnectionDialog } from './repo-connection-dialog';
import { Plug } from 'lucide-react';
import type { UseChatHelpers } from '@ai-sdk/react';
import type { ChatMessage } from '@/lib/types';

interface SuggestedActionsProps {
  chatId: string;
  sendMessage: UseChatHelpers<ChatMessage>['sendMessage'];
}

function PureSuggestedActions({ chatId, sendMessage }: SuggestedActionsProps) {
  const { data: session } = useSession();
  const [showRepoDialog, setShowRepoDialog] = useState(false);
  const hasConnectedRepo = Boolean(
    session?.user?.selectedSpace?.connectedRepoUrl,
  );

  const suggestedActions = [
    {
      title: 'Onboard',
      label: 'New Team Member',
      action:
        'Help me understand the current project structure and key components for onboarding',
    },
    {
      title: 'Specify',
      label: `Write User Stories`,
      action: `Initiate a Collaborative Example Mapping Session to gather open questions and define the next user stories. Announce the agenda, guide the team step by step, and create a new document for each story.`,
    },
    {
      title: 'Code',
      label: `Implement a User Story`,
      action: `Implement the following user story: \n`,
    },
    {
      title: 'Review',
      label: `Review a Pull Request`,
      action: `Review the following pull request: \n`,
    },
    {
      title: 'Document',
      label: `Create a Glossary`,
      action: `Create a glossary of ubiquitous language terms for our project`,
    },
    {
      title: 'Record',
      label: 'Architecture Decisions',
      action: 'Help me record the architecture decision (ADR) for:',
    },
  ];

  const connectRepoTile = (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 20 }}
      transition={{ delay: 0.02 }}
      key="connect-repository"
    >
      <Button
        variant="ghost"
        onClick={(event) => {
          event.preventDefault();
          setShowRepoDialog(true);
        }}
        className="text-left border rounded-xl px-4 py-3.5 text-sm flex-1 gap-1 sm:flex-col w-full h-auto justify-start items-start"
      >
        <span className="font-medium flex items-center gap-2">
          <Plug className="h-4 w-4" />
          Connect Repository
        </span>
        <span className="text-muted-foreground">
          Unlock code-aware assistance for this space
        </span>
      </Button>
    </motion.div>
  );

  return (
    <>
      <div className="grid sm:grid-cols-2 gap-2 w-full">
        {!hasConnectedRepo
          ? connectRepoTile
          : suggestedActions.map((suggestedAction, index) => (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                transition={{ delay: 0.05 * index }}
                key={`suggested-action-${suggestedAction.title}-${index}`}
                className={index > 1 ? 'hidden sm:block' : 'block'}
              >
                <Button
                  variant="ghost"
                  onClick={async (event) => {
                    event.preventDefault();
                    window.history.replaceState({}, '', `/chat/${chatId}`);

                    sendMessage({
                      role: 'user',
                      parts: [{ type: 'text', text: suggestedAction.action }],
                    });
                  }}
                  className="text-left border rounded-xl px-4 py-3.5 text-sm flex-1 gap-1 sm:flex-col w-full h-auto justify-start items-start"
                >
                  <span className="font-medium">{suggestedAction.title}</span>
                  <span className="text-muted-foreground">
                    {suggestedAction.label}
                  </span>
                </Button>
              </motion.div>
            ))}
      </div>

      <RepoConnectionDialog
        key={session?.user?.selectedSpace?.id}
        open={showRepoDialog}
        onOpenChange={setShowRepoDialog}
      />
    </>
  );
}

export const SuggestedActions = memo(PureSuggestedActions, () => true);
