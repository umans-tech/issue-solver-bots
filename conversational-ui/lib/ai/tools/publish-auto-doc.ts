import { z } from 'zod';
import { tool, type UIMessageStreamWriter } from 'ai';
import type { Session } from 'next-auth';
import {
  GetObjectCommand,
  PutObjectCommand,
  S3Client,
} from '@aws-sdk/client-s3';

import type { ChatMessage } from '@/lib/types';
import { generateUUID } from '@/lib/utils';

interface PublishAutoDocProps {
  session: Session;
  dataStream: UIMessageStreamWriter<ChatMessage>;
}

type Manifest = Record<string, Record<string, string>>;

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

const streamToString = async (stream: any): Promise<string> =>
  new Promise((resolve, reject) => {
    const chunks: any[] = [];
    stream.on('data', (chunk: any) => chunks.push(Buffer.from(chunk)));
    stream.on('error', (err: any) => reject(err));
    stream.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')));
  });

const loadManifest = async (
  s3Client: S3Client,
  bucket: string,
  key: string,
): Promise<Manifest> => {
  try {
    const res = await s3Client.send(
      new GetObjectCommand({ Bucket: bucket, Key: key }),
    );
    const bodyString = await streamToString(res.Body);
    const parsed = JSON.parse(bodyString);
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch {
    return {};
  }
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

      const cuduEndpoint = process.env.CUDU_ENDPOINT;
      if (!cuduEndpoint) {
        return { error: 'CUDU API endpoint is not configured' };
      }

      const latestCommitResponse = await fetch(
        `${cuduEndpoint}/repositories/${kbId}/auto-documentation/latest-indexed-commit`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'X-User-ID': session.user?.id || 'unknown',
          },
        },
      );

      if (!latestCommitResponse.ok) {
        const errorData = await latestCommitResponse.json().catch(() => ({}));
        return {
          error:
            errorData?.detail ||
            errorData?.error ||
            'Failed to resolve latest indexed commit',
        };
      }

      const latestCommitPayload = await latestCommitResponse.json();
      const commitSha = latestCommitPayload?.commit_sha;
      if (!commitSha) {
        return { error: 'Latest commit not found for this repository.' };
      }

      const promptResponse = await fetch(
        `${cuduEndpoint}/repositories/${kbId}/auto-documentation`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-User-ID': session.user?.id || 'unknown',
          },
          body: JSON.stringify({ docsPrompts: { [promptId]: prompt } }),
        },
      );

      if (!promptResponse.ok) {
        const errorData = await promptResponse.json().catch(() => ({}));
        return {
          error:
            errorData?.detail ||
            errorData?.error ||
            'Failed to configure auto-documentation prompts',
        };
      }

      const bucket = process.env.BLOB_BUCKET_NAME || '';
      const region = process.env.BLOB_REGION || '';
      const endpoint = process.env.BLOB_ENDPOINT || '';
      const accessKeyId = process.env.BLOB_ACCESS_KEY_ID || '';
      const secretAccessKey = process.env.BLOB_READ_WRITE_TOKEN || '';

      if (!bucket || !region || !accessKeyId || !secretAccessKey) {
        return { error: 'Docs storage is not configured.' };
      }

      const s3Client = new S3Client({
        region,
        endpoint,
        forcePathStyle: !!endpoint,
        credentials: {
          accessKeyId,
          secretAccessKey,
        },
      });

      const docKey = `base/${kbId}/docs/${commitSha}/${docPath}`;
      await s3Client.send(
        new PutObjectCommand({
          Bucket: bucket,
          Key: docKey,
          Body: bodyContent,
          ContentType: 'text/markdown',
        }),
      );

      const processId = generateUUID();
      const runId = generateUUID();
      const manifestKey = `base/${kbId}/docs/${commitSha}/__metadata__.json`;
      const manifest = await loadManifest(s3Client, bucket, manifestKey);
      const metadataUpdate: Record<string, string> = {
        origin: 'auto',
        process_id: processId,
        source: 'conversation',
      };
      if (chatId) metadataUpdate.chat_id = chatId;
      if (messageId) metadataUpdate.message_id = messageId;

      manifest[docPath] = {
        ...(manifest[docPath] || {}),
        ...metadataUpdate,
      };

      await s3Client.send(
        new PutObjectCommand({
          Bucket: bucket,
          Key: manifestKey,
          Body: JSON.stringify(manifest),
          ContentType: 'application/json',
        }),
      );

      const completionResponse = await fetch(
        `${cuduEndpoint}/repositories/${kbId}/auto-documentation/publish-completed`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-User-ID': session.user?.id || 'unknown',
          },
          body: JSON.stringify({
            promptId,
            codeVersion: commitSha,
            generatedDocuments: [docPath],
            processId,
            runId,
          }),
        },
      );

      if (!completionResponse.ok) {
        const errorData = await completionResponse.json().catch(() => ({}));
        return {
          error:
            errorData?.detail ||
            errorData?.error ||
            'Failed to record auto-doc publish',
        };
      }

      const encodedPath = docPath
        .split('/')
        .map((segment) => encodeURIComponent(segment))
        .join('/');
      const docUrl = `/docs/${encodeURIComponent(kbId)}/${encodedPath}?v=${encodeURIComponent(commitSha)}`;

      return {
        ok: true,
        title,
        knowledgeBaseId: kbId,
        commitSha,
        path: docPath,
        promptId,
        processId,
        runId,
        docUrl,
      };
    },
  });
