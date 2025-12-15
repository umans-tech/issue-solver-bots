import { z } from 'zod';
import type { Session } from 'next-auth';
import { tool, type UIMessageStreamWriter } from 'ai';
import type { ChatMessage } from '@/lib/types';

interface RemoteCodingAgentProps {
  session: Session;
  dataStream: UIMessageStreamWriter<ChatMessage>;
}

const issueSchema = z.object({
  title: z
    .string()
    .describe(
      'The title of the issue to be resolved. Must be a JSON string value.',
    ),
  description: z
    .string()
    .describe(
      'The description of the issue to be resolved. Must be a JSON string value.',
    ),
});

export const remoteCodingAgent = ({ session }: RemoteCodingAgentProps) =>
  tool({
    description:
      'A tool that launches a remote instance of a coding agent to resolve an issue by submitting a PR/MR. IMPORTANT: Use strict JSON format for parameters. Example: {"issue": {"title": "Fix bug in authentication", "description": "The login form shows incorrect error messages"}}',
    inputSchema: z.object({
      issue: issueSchema,
    }),
    execute: async ({ issue }) => {
      try {
        const knowledgeBaseId =
          // @ts-ignore - Accessing properties that TypeScript doesn't know about
          session.knowledgeBaseId ||
          session?.user?.selectedSpace?.knowledgeBaseId;

        if (!knowledgeBaseId) {
          return 'No knowledge base found for this user. Please connect a repository first.';
        }

        // Get the CUDU API endpoint from environment variables
        const cuduEndpoint = process.env.CUDU_ENDPOINT;

        if (!cuduEndpoint) {
          return 'CUDU API endpoint is not configured';
        }

        // Prepare the request body
        const requestBody = {
          knowledgeBaseId,
          issue,
        };

        // Send request to CUDU API
        const response = await fetch(`${cuduEndpoint}/resolutions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-User-ID': session.user?.id || 'unknown',
          },
          body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
          const errorData = await response.json();
          console.error('Error from CUDU API:', errorData);
          return `Failed to create resolution: ${errorData.detail || response.statusText}`;
        }

        const data = await response.json();
        return data;
      } catch (error) {
        console.error('Error in remote coding agent:', error);
        return 'An error occurred while processing the issue.';
      }
    },
  });
