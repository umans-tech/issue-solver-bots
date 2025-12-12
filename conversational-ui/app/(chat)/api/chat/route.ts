import { smoothStream, streamText, UIMessage, stepCountIs, createUIMessageStream, convertToModelMessages, JsonToSseTransformStream, type UIMessagePart } from 'ai';

import { auth } from '@/app/(auth)/auth';
import { myProvider } from '@/lib/ai/models';
import { systemPrompt } from '@/lib/ai/prompts';
import {
    createStreamId,
    deleteChatById,
    getChatById,
    getCurrentUserSpace,
    saveChat,
    saveMessages,
    updateChatTitleById
} from '@/lib/db/queries';
import { generateUUID, getMostRecentUserMessage } from '@/lib/utils';
import { generateTitleFromUserMessage } from '../../actions';
import { extractModel, recordTokenUsage } from '@/lib/token-usage';
import { createDocument } from '@/lib/ai/tools/create-document';
import { updateDocument } from '@/lib/ai/tools/update-document';
import { requestSuggestions } from '@/lib/ai/tools/request-suggestions';
import { getWeather } from '@/lib/ai/tools/get-weather';
import { codebaseAssistant } from '@/lib/ai/tools/codebase-assistant';
import { codebaseSearch } from '@/lib/ai/tools/codebase-search';
import { webSearch } from '@/lib/ai/tools/web-search';
import { remoteCodingAgent } from '@/lib/ai/tools/remote-coding-agent';
import { fetchWebpage } from '@/lib/ai/tools/fetch-webpage';
import { createResumableStreamContext, type ResumableStreamContext } from 'resumable-stream';
import { setController, deleteController } from '@/lib/stream/controller-registry';
import { after } from 'next/server';
import { codeRepositoryMCPClient } from "@/lib/ai/tools/github_mcp";
import { ChatMessage } from '@/lib/types';
import { checkChatEntitlements } from '@/lib/ai/entitlements';

export const maxDuration = 60;
const maxSteps = 40;
const maxRetries = 10;



let globalStreamContext: ResumableStreamContext | null = null;

export function getStreamContext() {
  if (!globalStreamContext) {
    try {
      globalStreamContext = createResumableStreamContext({
        waitUntil: after,
      });
    } catch (error: any) {
        console.log(error);
      if (error.message.includes('REDIS_URL')) {
        console.log(
          ' > Resumable streams are disabled due to missing REDIS_URL',
        );
      } else {
        console.error(error);
      }
    }
  }

  return globalStreamContext;
}

function sanitizeMessageParts(parts: UIMessagePart<any, any>[]) {
  return parts
    .filter((part) => (part as any)?.transient !== true)
    .map((part) => {
      const { id, providerMetadata, callProviderMetadata, ...rest } = part as Record<string, unknown>;
      const sanitized: Record<string, unknown> = { ...rest };

      if (part.type === 'text' || part.type === 'reasoning') {
        sanitized.state = 'done';
      } else if ('state' in part && typeof (part as any).state === 'string') {
        sanitized.state = (part as any).state === 'streaming' ? 'done' : (part as any).state;
      }

      return sanitized as UIMessagePart<any, any>;
    });
}

function findLatestAssistantMessage(messages: UIMessage[]) {
  return messages
    .filter((message) => message.role === 'assistant')
    .at(-1) ?? null;
}

export async function POST(request: Request) {
    const {
        id,
        messages,
        selectedChatModel,
        knowledgeBaseId,
    }: {
        id: string;
        messages: ChatMessage[];
        selectedChatModel: string;
        knowledgeBaseId?: string | null;
    } = await request.json();

    const session = await auth();

    if (!session || !session.user || !session.user.id) {
        return new Response('Unauthorized', { status: 401 });
    }

    const userMessage = getMostRecentUserMessage(messages);

    if (!userMessage) {
        return new Response('No user message found', { status: 400 });
    }

    const chat = await getChatById({ id });

    if (!chat) {
        const title = await generateTitleFromUserMessage({ message: userMessage });

        // Get current user's selected space
        const currentSpace = await getCurrentUserSpace(session.user.id);
        if (!currentSpace) {
          throw new Error('Unable to determine user space');
        }

        await saveChat({
          id,
          userId: session.user.id,
          title,
          spaceId: currentSpace.id
        });
    }

    // Enforce simple per-plan limits (inspired by Vercel AI chatbot entitlements)
    try {
      const plan = ((session.user as any).plan as string) || 'free';
      const entitlement = await checkChatEntitlements({ userId: session.user.id, plan });
      if (!entitlement.ok) {
        const explain = JSON.stringify({
          code: entitlement.reason,
          message:
            entitlement.reason === 'daily-limit'
              ? `Daily message limit reached (${entitlement.limitToday}).`
              : `Monthly message limit reached (${entitlement.limitMonth}).`,
          retryAt: entitlement.retryAt,
        });
        return new Response(explain, { status: 402, headers: { 'content-type': 'application/json' } });
      }
    } catch (e) {
      // Fail-open to avoid blocking users on transient errors
      console.warn('Entitlement check failed (continuing):', e);
    }

    await saveMessages({
        messages: [
            {
              chatId: id,
              id: userMessage.id,
              role: 'user',
              parts: userMessage.parts,
              attachments: [],//message.experimental_attachments ?? [],
              createdAt: new Date(),
            },
          ],
    });

    const streamId = generateUUID();

    const { chatModelProvider, chatModelName } = extractModel(selectedChatModel);

    await createStreamId({ streamId, chatId: id });
    // Ensure the assistant message uses a stable ID across normal/aborted flows
    const assistantMessageId = generateUUID();
    // Get current user's space for MCP context
    const currentSpace = await getCurrentUserSpace(session.user.id);
    const userContext = currentSpace ? {
        userId: session.user.id,
        spaceId: currentSpace.id
    } : undefined;

    // Initialize fresh MCP client with user context for this request
    // Declare up-front so TypeScript sees the identifier in the callbacks below
    let mcpClient: Awaited<ReturnType<typeof codeRepositoryMCPClient>>['client'] | null = null;
    let mcpClientClosed = false;

    const clientWrapper = await codeRepositoryMCPClient(userContext);
    mcpClient = clientWrapper.client;
    const mcpTools = await mcpClient.tools();

    const stream = createUIMessageStream({
        execute: async ({ writer: dataStream }) => {

            // Create a dedicated abort controller not tied to request.signal
            const abortController = new AbortController();
            // Register controller so Stop can cancel without breaking resumable refresh
            setController(streamId, abortController);

            const result = streamText({
                model: myProvider.languageModel(selectedChatModel),
                system: systemPrompt({ selectedChatModel }),
                messages: convertToModelMessages(messages),
                stopWhen: stepCountIs(maxSteps),
                maxRetries: maxRetries,
                // Use dedicated abort controller (not tied to browser disconnects)
                abortSignal: abortController.signal,
                providerOptions: {
                    openai: {
                        reasoningEffort: 'high',
                        reasoningSummary: 'detailed', // Explicitly request detailed reasoning summaries
                    }
                },
                experimental_activeTools: [
                    'getWeather',
                    'createDocument',
                    'updateDocument',
                    'requestSuggestions',
                    'codebaseAssistant',
                    'codebaseSearch',
                    'webSearch',
                    'remoteCodingAgent',
                    'fetchWebpage',
                    // @ts-ignore
                    ...clientWrapper.activeTools()
                ],
                experimental_transform: smoothStream({ chunking: 'word' }),
                tools: {
                    getWeather,
                    ...mcpTools,
                    createDocument: createDocument({ session, dataStream }),
                    updateDocument: updateDocument({ session, dataStream }),
                    requestSuggestions: requestSuggestions({
                        session,
                        dataStream,
                    }),
                    codebaseAssistant: codebaseAssistant({
                        session,
                        dataStream,
                    }),
                    codebaseSearch: codebaseSearch({
                        session: Object.assign({}, session, { knowledgeBaseId }),
                        dataStream,
                    }),
                    webSearch: webSearch({
                        session,
                        dataStream,
                    }),
                    remoteCodingAgent: remoteCodingAgent({
                        session: Object.assign({}, session, { knowledgeBaseId }),
                        dataStream,
                    }),
                    fetchWebpage: fetchWebpage({
                        session,
                        dataStream,
                    }),
                },
                experimental_telemetry: {
                    isEnabled: true,
                    functionId: 'stream-text',
                },
                onAbort: () => {},
            });
            
            result.consumeStream();
            
            dataStream.merge(
                result.toUIMessageStream({
                    sendReasoning: true,
                    sendSources: true,
                    messageMetadata: ({ part }) => {
                        if (part.type !== 'finish') return;
                        return {
                          usage: part.totalUsage,
                          providerMetadata: result.providerMetadata,
                        };
                    },
                }),
            );
        },
        // Use stable assistant message id so abort and normal flows align
        generateId: () => assistantMessageId,
        onFinish: async ({ messages: finishedMessages, responseMessage, isAborted }) => {
          try {
            if (!session.user?.id) {
              return;
            }

            const latestAssistant = findLatestAssistantMessage(finishedMessages);
            const baseParts = responseMessage.parts && responseMessage.parts.length > 0
              ? (responseMessage.parts as UIMessagePart<any, any>[])
              : (latestAssistant?.parts as UIMessagePart<any, any>[] | undefined);

            const sanitizedParts = baseParts ? sanitizeMessageParts(baseParts) : [];

            const assistantId = responseMessage.id
              ?? latestAssistant?.id
              ?? assistantMessageId;

            const partsToStore = isAborted
              ? sanitizedParts.filter((part) => part.type !== 'reasoning')
              : sanitizedParts;

            if (partsToStore.length > 0) {
              await saveMessages({
                messages: [
                  {
                    id: assistantId,
                    chatId: id,
                    role: responseMessage.role ?? latestAssistant?.role ?? 'assistant',
                    parts: partsToStore,
                    attachments: [],
                    createdAt: new Date(),
                  },
                ],
              });
            }

            if (!isAborted && partsToStore.length > 0 && chatModelProvider && chatModelName) {
              const metadata = responseMessage.metadata;
              if (metadata) {
                await recordTokenUsage({
                  messageId: assistantId,
                  provider: chatModelProvider,
                  model: chatModelName,
                  // @ts-ignore
                  rawUsageData: metadata.usage,
                  // @ts-ignore
                  providerMetadata: metadata.providerMetadata,
                });
              }
            }
          } catch (error) {
            console.error('Failed to save chat');
          } finally {
            deleteController(streamId);
            // Close MCP client to prevent connection leak
            if (!mcpClientClosed && mcpClient) {
              try {
                await mcpClient.close();
                mcpClientClosed = true;
              } catch (error) {
                console.error('Failed to close MCP client:', error);
              }
            }
          }
      },
        onError: (error) => {
            console.error('Error during streaming:', error);
            deleteController(streamId);
            // Close MCP client to prevent connection leak on error
            if (!mcpClientClosed && mcpClient) {
              mcpClient.close()?.catch((err: Error) => console.error('Failed to close MCP client on error:', err));
              mcpClientClosed = true;
            }
            return 'Oops, an error occured!';
        },
    });

    const streamContext = getStreamContext();

    if (streamContext) {
      return new Response(
        await streamContext.resumableStream(streamId, () => stream.pipeThrough(new JsonToSseTransformStream())),
      );
    } else {
      return new Response(stream.pipeThrough(new JsonToSseTransformStream()));
    }
}

export async function DELETE(request: Request) {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id) {
        return new Response('Not Found', { status: 404 });
    }

    const session = await auth();

    if (!session || !session.user) {
        return new Response('Unauthorized', { status: 401 });
    }

    try {
        const chat = await getChatById({ id });

        if (chat.userId !== session.user.id) {
            return new Response('Unauthorized', { status: 401 });
        }

        await deleteChatById({ id });

        return new Response('Chat deleted', { status: 200 });
    } catch (error) {
        return new Response('An error occurred while processing your request', {
            status: 500,
        });
    }
}

export async function PATCH(request: Request) {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id) {
        return new Response('Not Found', { status: 404 });
    }

    const session = await auth();

    if (!session || !session.user) {
        return new Response('Unauthorized', { status: 401 });
    }

    try {
        const chat = await getChatById({ id });

        if (!chat || chat.userId !== session.user.id) {
            return new Response('Unauthorized', { status: 401 });
        }

        const { title } = await request.json();

        if (!title || typeof title !== 'string' || title.trim() === '') {
            return new Response('Invalid title', { status: 400 });
        }

        await updateChatTitleById({ chatId: id, title: title.trim() });

        return new Response('Chat title updated', { status: 200 });
    } catch (error) {
        console.error('Error updating chat title:', error);
        return new Response('An error occurred while processing your request', {
            status: 500,
        });
    }
}
