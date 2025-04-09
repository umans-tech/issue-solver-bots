'use client';

import { startTransition, useMemo, useOptimistic, useState, useEffect } from 'react';
import { useLocalStorage } from 'usehooks-ts';

import { saveChatModelAsCookie } from '@/app/(chat)/actions';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { chatModels } from '@/lib/ai/models';
import { cn } from '@/lib/utils';

import { CheckCircleFillIcon, ChevronDownIcon } from './icons';

export function ModelSelector({
  selectedModelId,
  className,
}: {
  selectedModelId: string;
} & React.ComponentProps<typeof Button>) {
  const [open, setOpen] = useState(false);
  const [optimisticModelId, setOptimisticModelId] = useOptimistic(selectedModelId);
  const [storedModelId, setStoredModelId] = useLocalStorage('chat-model', selectedModelId);

  useEffect(() => {
    if (storedModelId !== selectedModelId) {
      setOptimisticModelId(storedModelId);
    }
  }, [storedModelId, selectedModelId, setOptimisticModelId]);

  const selectedChatModel = useMemo(
    () => chatModels.find((chatModel) => chatModel.id === optimisticModelId),
    [optimisticModelId],
  );

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger
        asChild
        className={cn(
          'w-fit data-[state=open]:bg-muted',
          className,
        )}
      >
        <Button 
          variant="ghost" 
          className="md:px-2 md:h-[34px] bg-muted hover:bg-muted text-muted-foreground text-sm"
        >
          {selectedChatModel?.name}
          <ChevronDownIcon size={16} />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="min-w-[300px] bg-muted border-muted">
        {chatModels.map((chatModel) => {
          const { id } = chatModel;

          return (
            <DropdownMenuItem
              key={id}
              onSelect={() => {
                setOpen(false);
                startTransition(() => {
                  setOptimisticModelId(id);
                  setStoredModelId(id);
                });
              }}
              className="gap-4 group/item flex flex-row justify-between items-center hover:bg-background"
              data-active={id === optimisticModelId}
            >
              <div className="flex flex-col gap-1 items-start">
                <div className="text-muted-foreground">{chatModel.name}</div>
                <div className="text-xs text-muted-foreground/70">
                  {chatModel.description}
                </div>
              </div>

              <div className="text-muted-foreground opacity-0 group-data-[active=true]/item:opacity-100">
                <CheckCircleFillIcon />
              </div>
            </DropdownMenuItem>
          );
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
