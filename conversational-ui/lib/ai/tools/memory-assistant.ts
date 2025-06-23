import { z } from 'zod';
import { tool } from 'ai';
import { generateText } from 'ai';
import { Session } from 'next-auth';
import { DataStreamWriter } from 'ai';
import { myProvider } from '@/lib/ai/models';
import { 
  getMemoryByUserSpace, 
  upsertMemory, 
  getCurrentUserSpace 
} from '@/lib/db/queries';

// Define the action type enum with detailed descriptions
const ActionTypeEnum = z.enum([
  'read',
  'write', 
  'edit'
]);

// Interface for memoryAssistant props
interface MemoryAssistantProps {
  session: Session;
  dataStream: DataStreamWriter;
}

export const memoryAssistant = ({ session }: MemoryAssistantProps) => tool({
  description: `Manage persistent memory across conversations within your current space. This tool allows you to store, retrieve, and modify important information that should be remembered between different chat sessions.

**When to use this tool:**
- Store important user preferences, project context, or recurring information
- Remember key decisions, patterns, or insights from previous conversations  
- Track ongoing tasks, goals, or project status across sessions
- Keep notes about code patterns, architectural decisions, or domain knowledge
- Store user-specific context like coding style preferences or project requirements

**Memory is scoped per space** - each space has its own isolated memory that won't interfere with other projects.`,

  parameters: z.object({
    action: ActionTypeEnum.describe(
      `The memory operation to perform:

**read** - Retrieve and display the complete current memory contents
- Use when you need to understand what information is already stored
- Returns the full memory content for review
- No additional parameters required

**write** - Replace the entire memory with new content (WARNING: overwrites existing data)
- Use when starting fresh or when you want to completely restructure stored information
- Requires 'content' parameter with the new memory content
- Will warn if overwriting existing content
- Best for initial memory setup or major reorganization

**edit** - Perform targeted string replacement within existing memory
- Use for precise updates, corrections, or additions to specific parts of memory
- Requires 'old_string' (exact text to find) and 'new_string' (replacement text)
- Safer than 'write' for small changes as it preserves surrounding content
- Will error if the exact text to replace is not found
- Will warn if multiple matches exist to prevent unintended changes`
    ),
    content: z.string().optional().describe(
      `Full text content to store when using 'write' action. 
      
Should contain well-structured information like:
- User preferences and context
- Project-specific knowledge  
- Important decisions or patterns
- Ongoing tasks or goals
- Code style guidelines
- Domain knowledge or terminology

Ignored for 'read' and 'edit' actions.`
    ),
    old_string: z.string().optional().describe(
      `Exact text to find and replace when using 'edit' action.
      
**Important:** Must match the text exactly, including:
- Exact capitalization and punctuation
- All whitespace (spaces, tabs, newlines)  
- Complete phrases or sentences for reliability

If unsure of exact text, use 'read' action first to see current content.
Ignored for 'read' and 'write' actions.`
    ),
    new_string: z.string().optional().describe(
      `Replacement text to insert when using 'edit' action.
      
This text will replace the 'old_string' exactly. Can be:
- Updated information
- Additional details  
- Corrections
- Empty string to delete content

Ignored for 'read' and 'write' actions.`
    ),
  }),
  execute: async ({ action, content, old_string, new_string }) => {
    const userId = session.user?.id;
    if (!userId) {
      return 'Error: User not authenticated';
    }

    try {
      // Get current user space
      const currentSpace = await getCurrentUserSpace(userId);
      if (!currentSpace) {
        return 'Error: Unable to determine current workspace';
      }

      const spaceId = currentSpace.id;

      if (action === 'read') {
        return await readMemory(userId, spaceId);
      } else if (action === 'write') {
        if (!content) {
          return 'Error: Content parameter is required for write action';
        }
        return await writeMemory(userId, spaceId, content);
      } else if (action === 'edit') {
        if (!old_string || !new_string) {
          return 'Error: Both old_string and new_string parameters are required for edit action';
        }
        return await editMemory(userId, spaceId, old_string, new_string);
      }

      return `Error: Unknown action '${action}'. Valid actions are: read, write, edit`;
    } catch (error) {
      console.error('Memory assistant error:', error);
      return 'Error: Failed to process memory operation. Please try again.';
    }
  },
});

async function readMemory(userId: string, spaceId: string): Promise<string> {
  const memory = await getMemoryByUserSpace(userId, spaceId);
  
  if (!memory || !memory.content) {
    return 'No memory stored yet for this workspace. Use the "write" action to create initial memory content.';
  }
  
  return `**Current Memory Content:**\n\n${memory.content}\n\n---\n*Last updated: ${memory.updatedAt.toLocaleString()}*`;
}

async function writeMemory(userId: string, spaceId: string, content: string): Promise<string> {
  const existingMemory = await getMemoryByUserSpace(userId, spaceId);
  
  // Generate AI summary of the content, providing existing summary for context
  const summary = await generateMemorySummary(content, existingMemory?.summary);
  
  await upsertMemory(userId, spaceId, content, summary);
  
  if (existingMemory && existingMemory.content) {
    return `**Warning:** Overwrote existing memory content.\n\n**Previous content was:**\n${existingMemory.content.substring(0, 200)}${existingMemory.content.length > 200 ? '...' : ''}\n\n**Memory has been updated successfully with new content.**`;
  }
  
  return '**Memory updated successfully.** The content is now stored and will be available in future conversations within this workspace.';
}

async function editMemory(userId: string, spaceId: string, oldString: string, newString: string): Promise<string> {
  const memory = await getMemoryByUserSpace(userId, spaceId);
  
  if (!memory || !memory.content) {
    return 'Error: No memory content exists to edit. Use "write" action to create initial content first.';
  }
  
  if (!memory.content.includes(oldString)) {
    return `Error: Text not found in memory. The exact string "${oldString}" does not exist.\n\nUse "read" action to see current content, then try again with exact text.`;
  }
  
  // Check for multiple occurrences
  const occurrences = (memory.content.match(new RegExp(escapeRegExp(oldString), 'g')) || []).length;
  if (occurrences > 1) {
    return `Warning: Found ${occurrences} occurrences of "${oldString}" in memory. Please use a more specific string that uniquely identifies the text you want to replace to avoid unintended changes.`;
  }
  
  const newContent = memory.content.replace(oldString, newString);
  const summary = await generateMemorySummary(newContent, memory.summary);
  
  await upsertMemory(userId, spaceId, newContent, summary);
  
  return `**Memory edited successfully.** Replaced 1 occurrence of the specified text.\n\n**Change made:**\n- **Old:** "${oldString}"\n- **New:** "${newString}"`;
}

async function generateMemorySummary(content: string, previousSummary?: string): Promise<string> {
  try {
    if (!content || content.trim().length === 0) {
      return 'Empty memory';
    }

    // If content is already short, use it as the summary
    if (content.length <= 300) {
      return content.trim();
    }

    // Construct prompt based on whether we have a previous summary
    const prompt = previousSummary 
      ? `You are updating a memory summary. Analyze the current memory content and determine if the existing summary needs to be updated.

**Current Memory Content:**
${content}

**Existing Summary:**
${previousSummary}

**Instructions:**
- If the changes are minor (typos, small additions, formatting) and don't significantly change the meaning, respond with: KEEP_EXISTING
- If there are significant changes that warrant a new summary, create a concise summary (2-3 sentences, max 300 characters)
- Focus on the most important information that would help understand the context in future conversations

**Response:**`
      : `Create a concise summary (2-3 sentences, max 300 characters) of the following memory content. Focus on the most important information that would help understand the context in future conversations:

${content}

Summary:`;

    const { text } = await generateText({
      model: myProvider.languageModel('coding-model-large'),
      prompt,
    });

    const result = text.trim();
    
    // If AI decided to keep existing summary, return it
    if (result === 'KEEP_EXISTING' && previousSummary) {
      return previousSummary;
    }
    
    return result || content.substring(0, 300);
  } catch (error) {
    console.error('Error generating memory summary:', error);
    // Fallback: if we have a previous summary and there's an error, keep it
    if (previousSummary) {
      return previousSummary;
    }
    // Otherwise fallback to truncated content
    return content.length > 300 ? content.substring(0, 300) + '...' : content;
  }
}

function escapeRegExp(string: string): string {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}