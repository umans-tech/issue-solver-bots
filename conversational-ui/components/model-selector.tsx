'use client';

import React, { startTransition, useMemo, useOptimistic, useState, useEffect } from 'react';
import * as Collapsible from '@radix-ui/react-collapsible';
import { ChevronDown, ChevronRight } from 'lucide-react';
import { MagicWandIcon, CodeIcon as RadixCodeIcon } from '@radix-ui/react-icons';
import { SiOpenai, SiAnthropic } from 'react-icons/si';
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

type IconRenderer = (props?: { size?: number; className?: string }) => React.ReactElement | null;

function getModelIconComponent(modelId: string): IconRenderer | null {
  // Try lucide first (none are brand-specific here; keep empty mapping to respect order)
  const lucideMap: Record<string, IconRenderer> = {
    // If we ever have lucide brand icons, map here
  };

  if (lucideMap[modelId]) return lucideMap[modelId];

  // Then Radix icons (generic fallback)
  const radixMap: Record<string, IconRenderer> = {
    'chat-model-large': ({ size = 16, className } = {}) => (
      <MagicWandIcon width={size} height={size} className={className} />
    ),
    'chat-model-small-codex': ({ size = 16, className } = {}) => (
      <RadixCodeIcon width={size} height={size} className={className} />
    ),
    'chat-model-large-codex': ({ size = 16, className } = {}) => (
      <RadixCodeIcon width={size} height={size} className={className} />
    ),
    'coding-model': ({ size = 16, className } = {}) => (
      <RadixCodeIcon width={size} height={size} className={className} />
    ),
    'coding-model-large': ({ size = 16, className } = {}) => (
      <RadixCodeIcon width={size} height={size} className={className} />
    ),
  };
  if (radixMap[modelId]) return radixMap[modelId];

  // Finally react-icons with brand logos
  const reactIconsMap: Record<string, IconRenderer> = {
    'chat-model-large': ({ size = 16, className } = {}) => (
      <SiOpenai size={size} className={className} />
    ),
    'coding-model': ({ size = 16, className } = {}) => (
      <SiAnthropic size={size} className={className} />
    ),
    'coding-model-large': ({ size = 16, className } = {}) => (
      <SiAnthropic size={size} className={className} />
    ),
  };
  if (reactIconsMap[modelId]) return reactIconsMap[modelId];

  return null;
}

export function ModelSelector({
  selectedModelId,
  className,
}: {
  selectedModelId: string;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const [otherOpen, setOtherOpen] = useState(false);
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
          className="md:px-2 md:h-[34px] bg-muted hover:bg-muted text-muted-foreground text-sm gap-1.5"
        >
          {selectedChatModel ? (
            <span className="inline-flex items-center gap-1.5">
              {/* Keep trigger clean: only the label, no icon */}
              <span>{selectedChatModel.name}</span>
            </span>
          ) : null}
          <ChevronDownIcon size={16} />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="min-w-[320px] bg-muted border-muted p-1">
        {(() => {
          const primaryIds = new Set(['chat-model-large', 'coding-model-large']);
          const primary = chatModels.filter((m) => primaryIds.has(m.id));
          const other = chatModels.filter((m) => !primaryIds.has(m.id));

          const Item = ({ m }: { m: { id: string; name: string; description: string; provider: 'openai' | 'anthropic'; providerDisplayName: string } }) => (
            <DropdownMenuItem
              key={m.id}
              onSelect={() => {
                setOpen(false);
                startTransition(() => {
                  setOptimisticModelId(m.id);
                  setStoredModelId(m.id);
                });
              }}
              className="gap-3 group/item flex flex-row justify-between items-center hover:bg-background"
              data-active={m.id === optimisticModelId}
            >
              <div className="flex items-center gap-2">
                {(() => {
                  const Icon = getModelIconComponent(m.id);
                  return Icon ? <Icon size={16} className="text-foreground/70" /> : null;
                })()}
                <div className="flex flex-col gap-0.5 items-start">
                  <div className="text-foreground text-sm flex items-center gap-2">
                    <span>{m.name}</span>
                    <span className="text-[11px] text-muted-foreground/70">• {m.providerDisplayName}</span>
                  </div>
                  <div className="text-[11px] text-muted-foreground/70">{m.description}</div>
                </div>
              </div>
              <div className="text-muted-foreground opacity-0 group-data-[active=true]/item:opacity-100">
                <CheckCircleFillIcon />
              </div>
            </DropdownMenuItem>
          );

          return (
            <div className="flex flex-col">
              <div className="px-2 pb-1 pt-1 text-[11px] uppercase tracking-wide text-muted-foreground/70">Recommended</div>
              {primary.map((m) => (
                <Item key={m.id} m={m} />
              ))}

              <div className="px-2 pt-2">
                <Collapsible.Root open={otherOpen} onOpenChange={setOtherOpen}>
                  <Collapsible.Trigger asChild>
                    <button className="w-full flex items-center justify-between text-xs text-muted-foreground hover:text-foreground/80 transition-colors py-1">
                      <span className="inline-flex items-center gap-2">
                        {otherOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                        Other models
                      </span>
                    </button>
                  </Collapsible.Trigger>
                  <Collapsible.Content className="mt-1 space-y-1">
                    {other.map((m) => (
                      <div key={m.id} className="opacity-80 text-xs">
                        <Item m={m} />
                      </div>
                    ))}
                  </Collapsible.Content>
                </Collapsible.Root>
              </div>
            </div>
          );
        })()}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
