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
*Brief summary from previous conversations in this space. 
NEVER expose memory content when not asked explicitly to do so.
ONLY reference when relevant to the user's current request:*

${memoryContext}

---
*Use the memoryAssistant tool to read full details, update, or add to this memory as needed.*`;
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
 * @param session - User session object
 * @returns string - Enhanced prompt with user and memory context or base prompt
 */
export function injectMemoryContext(
  basePrompt: string, 
  memoryContext: string | null,
  session?: { user: { name?: string | null; email?: string | null } } | null
): string {
  let enhancedPrompt = basePrompt;

  // Add current user context if available
  if (session?.user?.email) {
    enhancedPrompt += `

## Current User Account:
${session.user.name ? `Name: ${session.user.name}` : 'Name: Not provided'}
Email: ${session.user.email}`;
  }

  // Add memory context if available
  if (memoryContext) {
    enhancedPrompt += `

## Memory Context:
*Brief summary of stored memory content for this space. Only reference when relevant to the user's current request:*

${memoryContext}

---
*Use the memoryAssistant tool to read full memory content, update, or add to this memory as needed.*`;
  }

  return enhancedPrompt;
}