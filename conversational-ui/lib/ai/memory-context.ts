import { getMemorySummary } from '@/lib/db/queries';

/**
 * Generates enhanced system prompt with memory context injection
 * @param basePrompt - The base system prompt
 * @param userId - The user ID
 * @param spaceId - The current space ID
 * @returns Promise<string> - Enhanced prompt with memory context or base prompt
 */
export async function enhancePromptWithMemory(
  basePrompt: string,
  userId: string,
  spaceId: string | null
): Promise<string> {
  // If no space context, return base prompt
  if (!spaceId) {
    return basePrompt;
  }

  try {
    // Get memory summary for the user-space pair
    const memoryContext = await getMemorySummary(userId, spaceId);
    
    // If no memory exists, return base prompt
    if (!memoryContext) {
      return basePrompt;
    }

    // Inject memory context into the prompt
    return `${basePrompt}

## Memory Context:
*The following information has been stored from previous conversations in this space:*

${memoryContext}

---
*Use the memoryAssistant tool to read, update, or add to this memory as needed.*`;
  } catch (error) {
    console.error('Error enhancing prompt with memory:', error);
    // Fallback to base prompt if memory retrieval fails
    return basePrompt;
  }
}

/**
 * Alternative function that takes the memory context directly
 * @param basePrompt - The base system prompt
 * @param memoryContext - Pre-fetched memory context
 * @returns string - Enhanced prompt with memory context or base prompt
 */
export function injectMemoryContext(
  basePrompt: string, 
  memoryContext: string | null
): string {
  if (!memoryContext) {
    return basePrompt;
  }

  return `${basePrompt}

## Memory Context:
*The following information has been stored from previous conversations in this space:*

${memoryContext}

---
*Use the memoryAssistant tool to read, update, or add to this memory as needed.*`;
}