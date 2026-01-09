import { z } from 'zod';
import { tool, type UIMessageStreamWriter } from 'ai';
import type { Session } from 'next-auth';
import type { ChatMessage } from '@/lib/types';

interface PublishAutoDocProps {
  session: Session;
  dataStream: UIMessageStreamWriter<ChatMessage>;
}

type DocPathResult = { docPath: string; promptId: string } | { error: string };

const sanitizeDocPath = (value: string): DocPathResult => {
  if (!value || typeof value !== 'string') {
    return { error: 'path is required' };
  }

  const trimmed = value
    .trim()
    .replace(/^\/+/, '')
    .replace(/\\+/g, '/');

  if (!trimmed) {
    return { error: 'path is required' };
  }

  const segments = trimmed.split('/');
  if (segments.some((segment) => segment === '' || segment === '.' || segment === '..')) {
    return { error: 'path contains invalid segments' };
  }

  const hasMarkdownExtension = trimmed.toLowerCase().endsWith('.md');
  const docPath = hasMarkdownExtension ? trimmed : `${trimmed}.md`;
  const promptId = hasMarkdownExtension ? trimmed.slice(0, -3) : trimmed;

  return { docPath, promptId };
};

export const publishAutoDoc = ({ session }: PublishAutoDocProps) =>
  tool({
    description:
      'Publish an approved assistant response as auto documentation in the Docs tab. Use when the user explicitly asks to turn the response into auto documentation.',
    inputSchema: z.object({
      title: z.string().describe('Short human-readable title for the doc.'),
      path: z
        .string()
        .describe(
          'Doc path relative to the docs root. Supports folders using / (example: architecture/overview.md).',
        ),
      content: z
        .string()
        .describe('The final approved markdown content to publish.'),
      promptDescription: z
        .string()
        .describe('Prompt inferred from the conversation to regenerate this doc.'),
      source: z
        .record(z.string())
        .optional()
        .describe('Optional source metadata describing where this doc came from.'),
      knowledgeBaseId: z
        .string()
        .optional()
        .describe('Override knowledge base ID if needed.'),
      chatId: z.string().optional().describe('Chat identifier for traceability.'),
      messageId: z
        .string()
        .optional()
        .describe('Message identifier for traceability.'),
    }),
    execute: async ({
      title,
      path,
      content,
      promptDescription,
      source,
      knowledgeBaseId,
      chatId,
      messageId,
    }) => {
      const kbId =
        knowledgeBaseId ||
        // @ts-expect-error - Accessing properties that TypeScript doesn't know about
        session.knowledgeBaseId ||
        session?.user?.selectedSpace?.knowledgeBaseId;

      if (!kbId) {
        return {
          error: 'No knowledge base found for this user. Please connect a repository first.',
        };
      }

      const prompt = promptDescription?.trim();
      if (!prompt) {
        return { error: 'promptDescription is required' };
      }

      const bodyContent = content?.trim();
      if (!bodyContent) {
        return { error: 'content is required' };
      }

      const pathResult = sanitizeDocPath(path);
      if ('error' in pathResult) {
        return { error: pathResult.error };
      }

      const { docPath, promptId } = pathResult;
      const sourceMetadata: Record<string, string> = {
        ...(source ?? {}),
      };
      if (chatId) {
        sourceMetadata.chat_id ??= chatId;
      }
      if (messageId) {
        sourceMetadata.message_id ??= messageId;
      }

      const cuduEndpoint = process.env.CUDU_ENDPOINT;
      if (!cuduEndpoint) {
        return { error: 'CUDU API endpoint is not configured' };
      }

      const publishResponse = await fetch(
        `${cuduEndpoint}/repositories/${kbId}/auto-documentation/publish`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-User-ID': session.user?.id || 'unknown',
          },
          body: JSON.stringify({
            path: docPath,
            content: bodyContent,
            promptDescription: prompt,
            title,
            source: Object.keys(sourceMetadata).length ? sourceMetadata : undefined,
            chatId,
            messageId,
          }),
        },
      );

      const publishPayload = await publishResponse.json().catch(() => ({}));

      if (!publishResponse.ok) {
        return {
          error:
            publishPayload?.detail ||
            publishPayload?.error ||
            'Failed to publish auto documentation',
        };
      }

      const commitSha = publishPayload?.code_version;
      const encodedPath = docPath
        .split('/')
        .map((segment) => encodeURIComponent(segment))
        .join('/');
      const docUrl = commitSha
        ? `/docs/${encodeURIComponent(kbId)}/${encodedPath}?v=${encodeURIComponent(commitSha)}`
        : `/docs/${encodeURIComponent(kbId)}/${encodedPath}`;

      return {
        ok: true,
        title,
        knowledgeBaseId: kbId,
        commitSha,
        path: docPath,
        promptId,
        processId: publishPayload?.process_id,
        runId: publishPayload?.run_id,
        docUrl,
      };
    },
  });
