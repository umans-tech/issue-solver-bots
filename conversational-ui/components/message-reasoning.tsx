'use client';

import { useState, useMemo } from 'react';
import { ChevronDownIcon } from './icons';
import { motion, AnimatePresence } from 'framer-motion';
import { Markdown } from './markdown';

interface MessageReasoningProps {
  isLoading: boolean;
  reasoning: string;
  isStreaming?: boolean;
}


export function MessageReasoning({
  isLoading,
  reasoning,
  isStreaming = false,
}: MessageReasoningProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const hasContent = reasoning && reasoning.trim().length > 0;

  const variants = {
    collapsed: {
      height: 0,
      opacity: 0,
      marginTop: 0,
      marginBottom: 0,
    },
    expanded: {
      height: 'auto',
      opacity: 1,
      marginTop: '1rem',
      marginBottom: '0.5rem',
    },
  };

  return (
    <div className="flex flex-col">
      {/* Show animated state while streaming, completed state when done */}
      {isStreaming && hasContent ? (
        <div className="flex flex-row gap-2 items-center">
          <span className="animate-pulse font-medium text-muted-foreground">Reasoning...</span>
          <div
            className="cursor-pointer"
            onClick={() => {
              setIsExpanded(!isExpanded);
            }}
          >
            <ChevronDownIcon />
          </div>
        </div>
      ) : isStreaming && !hasContent ? (
        <div className="flex flex-row gap-2 items-center">
          <span className="animate-pulse font-medium text-muted-foreground">Reasoning...</span>
        </div>
      ) : hasContent ? (
        <div className="flex flex-row gap-2 items-center">
          <div className="font-medium">Reasoned for a few seconds</div>
          <div
            className="cursor-pointer"
            onClick={() => {
              setIsExpanded(!isExpanded);
            }}
          >
            <ChevronDownIcon />
          </div>
        </div>
      ) : null}

      <AnimatePresence initial={false}>
        {isExpanded && hasContent && (
          <motion.div
            key="content"
            initial="collapsed"
            animate="expanded"
            exit="collapsed"
            variants={variants}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            style={{ overflow: 'hidden' }}
            className="pl-4 text-zinc-600 dark:text-zinc-400 border-l flex flex-col gap-4"
          >
            <Markdown>{reasoning}</Markdown>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
