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
- **PRIORITY: Identify user's technical background** (engineer/developer vs non-technical user) as early as possible
- **Communication preferences**: When users express how they want information presented or their preferred interaction style
- **User corrections or feedback**: When users correct your approach or specify preferences about how to work
- Store comprehensive conversation summaries with appropriate technical detail level based on user background
- Remember user preferences, communication style, and specific requirements they've mentioned
- Track ongoing tasks, project evolution, and decisions across sessions (technical or business-focused)
- Document approaches used in the project (code patterns for developers, high-level concepts for non-technical users)
- Keep detailed records of problems encountered, solutions implemented, and lessons learned
- Store context about the user's working style, preferred explanation depth, and project goals
- Remember specific details relevant to their role (file locations for developers, feature descriptions for non-technical users)

**Memory Structure Guidelines:**
Store information in a structured format similar to detailed session notes, including:
- **User Profile**: Technical background (developer/engineer vs non-technical), experience level, and role
- Primary requests and user intent (business goals vs technical implementation)
- Appropriate level of detail (technical concepts for developers, high-level explanations for non-technical users)
- File paths and code sections for developers, feature descriptions and business impact for non-technical users
- User feedback, corrections, and communication preferences (technical depth, explanation style)
- Problem-solving approaches and solutions (code-level for developers, conceptual for non-technical users)
- Project context and decisions (architectural for developers, strategic for non-technical users)

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
      
Should contain comprehensive, well-structured information including:

**User Profile (CRITICAL - IDENTIFY EARLY):**
- Technical background: Developer/Engineer vs Non-technical user (business, product, design, etc.)
- Experience level and specific expertise areas
- Role in the project and decision-making authority
- Preferred communication style and explanation depth

**Conversation Analysis:**
- Primary requests and user intent (technical implementation vs business goals)
- Implementation details (technical for developers, high-level concepts for non-technical users)
- User feedback, corrections, and specific preferences
- Key decisions made and reasoning behind them

**Project Context (ADAPT TO USER BACKGROUND):**
- For Developers: File paths and code sections (with line numbers like file:123), code patterns, technical approaches
- For Non-technical: Feature descriptions, business impact, user experience considerations
- Database schema, API endpoints, and system integrations (technical detail level based on user)
- Error patterns encountered and solutions implemented

**User Preferences:**
- Technical detail preference (deep technical vs high-level explanations)
- Communication style and preferred level of detail
- Project goals and priorities (technical vs business focused)
- Working patterns and methodologies

**Documentation (ROLE-APPROPRIATE):**
- For Developers: Tool implementations, database migrations, component structures, integration details
- For Non-technical: Feature specifications, user stories, business requirements, workflow descriptions

Structure the content like detailed session notes that would help future conversations understand the full context of the project and user interactions.

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

    // Construct prompt based on whether we have a previous summary
    const summaryGuidelines = `Create a comprehensive but concise summary that captures:
- **User's technical background and expertise level** (CRITICAL for appropriate communication)
- Primary requests and user intent (technical vs business focused)
- Implementation details and approaches (adapt complexity to user background)
- User preferences, standards, and specific requirements
- Key information relevant to user role (code locations for developers, business requirements for non-technical)
- Important decisions, problems encountered, and solutions
- Project context and patterns (technical or strategic focus)
- Communication style and preferred explanation depth`;

    const prompt = previousSummary 
      ? `You are updating a memory summary for an AI assistant's persistent memory system.

**Current Memory Content:**
${content}

**Existing Summary:**
${previousSummary}

**Task:** 
${summaryGuidelines}

If the changes are minor (typos, small formatting, or additions that don't change the core meaning), return the existing summary exactly as-is. If there are significant changes, create a new summary that helps future AI assistants understand the full context of user interactions and project details.

**Response (return existing summary unchanged OR provide comprehensive new summary):**`
      : `Create a comprehensive but concise summary of the following memory content for an AI assistant's persistent memory system.

**Memory Content:**
${content}

**Task:**
${summaryGuidelines}

Structure the summary to provide rich context for future conversations while keeping it concise.

**Summary:**`;

    const { text } = await generateText({
      model: myProvider.languageModel('coding-model-large'),
      prompt,
    });

    const result = text.trim();
    return result || content;
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