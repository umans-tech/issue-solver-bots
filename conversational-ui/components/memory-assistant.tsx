'use client';

import { Brain } from 'lucide-react';

export interface MemoryAssistantProps {
  result?: string;
  action?: string;
  content?: string;
  oldString?: string;
  newString?: string;
}

export const MemoryAssistantAnimation = () => (
  <div className="flex flex-col w-full">
    <div className="text-muted-foreground flex items-center gap-2">
      <Brain size={16} />
      <span className="animate-pulse">Managing memory...</span>
    </div>
  </div>
);

export function MemoryAssistant({ result, action, content, oldString, newString }: MemoryAssistantProps) {
  
  if (!result) {
    return null;
  }
  
  // Parse the action from the result text to determine the operation
  const getActionType = () => {
    const resultLower = result.toLowerCase();
    if (resultLower.includes('memory updated successfully') || resultLower.includes('overwrote')) {
      return 'write';
    } else if (resultLower.includes('edited successfully') || resultLower.includes('replaced')) {
      return 'edit';
    } else if (resultLower.includes('current memory content') || resultLower.includes('no memory stored')) {
      return 'read';
    }
    return 'unknown';
  };

  const actionType = getActionType();
  

  const getActionLabel = () => {
    switch (actionType) {
      case 'read': return 'Retrieved memory from space';
      case 'write': return 'Stored information in memory';
      case 'edit': return 'Updated memory content';
      default: return 'Performed memory operation';
    }
  };

  const getActionColor = () => {
    // Use consistent muted foreground like other tools
    return 'text-muted-foreground';
  };

  return (
    <div className="mt-1">
      {/* Action label only */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-muted-foreground">
          <Brain size={16} />
        </span>
        <span className={`${getActionColor()}`}>{getActionLabel()}</span>
      </div>
    </div>
  );
}