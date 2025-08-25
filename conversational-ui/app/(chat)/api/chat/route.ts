import { smoothStream, streamText, UIMessage, stepCountIs, createUIMessageStream, convertToModelMessages, JsonToSseTransformStream, } from 'ai';

import { auth } from '@/app/(auth)/auth';
import { myProvider } from '@/lib/ai/models';
import { systemPrompt } from '@/lib/ai/prompts';
import {
    createStreamId,
    deleteChatById,
    getChatById,
    getCurrentUserSpace,
    getMessagesByChatId,
    getStreamIdsByChatId,
    saveChat,
    saveMessages,
    updateChatTitleById
} from '@/lib/db/queries';
import { generateUUID, getMostRecentUserMessage, getTrailingMessageId, } from '@/lib/utils';
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
import { Chat } from '@/lib/db/schema';
import { createResumableStreamContext, type ResumableStreamContext } from 'resumable-stream';
import { after } from 'next/server';
import { differenceInSeconds } from 'date-fns';
import { codeRepositoryMCPClient } from "@/lib/ai/tools/github_mcp";
import { ChatMessage } from '@/lib/types';

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
    await createStreamId({ streamId, chatId: id });
    // Get current user's space for MCP context
    const currentSpace = await getCurrentUserSpace(session.user.id);
    const userContext = currentSpace ? {
        userId: session.user.id,
        spaceId: currentSpace.id
    } : undefined;
    
    // Initialize fresh MCP client with user context for this request
    const clientWrapper = await codeRepositoryMCPClient(userContext);
    const mcpClient = clientWrapper.client;
    const mcpTools = await mcpClient.tools();

    const stream = createUIMessageStream({
        execute: async ({ writer: dataStream }) => {
            
            // Collect sources written to the dataStream
            // const collectedSources: Array<{ sourceType: 'url'; id: string; url: string; title?: string; providerMetadata?: any }> = [];

            // // Wrap dataStream.writeSource to collect sources
            // const originalWriteSource = dataStream.writeSource.bind(dataStream);
            // dataStream.writeSource = (source) => {
            //     collectedSources.push(source);
            //     return originalWriteSource(source);
            // };

            const result = streamText({
                model: myProvider.languageModel(selectedChatModel),
                system: systemPrompt({ selectedChatModel }),
                messages: convertToModelMessages(messages),
                stopWhen: stepCountIs(maxSteps),
                maxRetries: maxRetries,
                toolCallStreaming: true,
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
            });
            
            result.consumeStream();
            
            dataStream.merge(
                result.toUIMessageStream({
                    sendReasoning: true,
                }),
            );
        },
        generateId: generateUUID,
        onFinish: async ({ messages, responseMessage}) => {//, usage, providerMetadata }) => {
          if (session.user?.id) {
              try {
                  const assistantId = getTrailingMessageId({
                      messages: messages.filter(
                        (message) => message.role === 'assistant',
                      ),
                    });

                    if (!assistantId) {
                      throw new Error('No assistant message found!');
                    }

                  // Add collected sources to the message parts
                  const messageParts = [...(responseMessage.parts || [])];
                  // for (const source of collectedSources) {
                  //     messageParts.push({
                  //         type: 'source',
                  //         source: source,
                  //     });
                  // }

                  await saveMessages({
                      messages: [
                          {
                            id: assistantId,
                            chatId: id,
                            role: responseMessage.role,
                            parts: messageParts,
                            attachments: [],//responseMessage.experimental_attachments ?? [],
                            createdAt: new Date(),
                          },
                      ],
                  });

                  // // Record token usage if available
                  // if (usage && assistantId) {
                  //     const { chatModelProvider, chatModelName } = extractModel(selectedChatModel)
                  //     await recordTokenUsage({
                  //         messageId: assistantId,
                  //         provider: chatModelProvider,
                  //         model: chatModelName,
                  //         rawUsageData: usage,
                  //         providerMetadata: providerMetadata,
                  //     });
                  // }
              } catch (error) {
                  console.error('Failed to save chat');
              }
          }
      },
        onError: (error) => {
            console.error('Error during streaming:', error);
            return 'Oops, an error occured!';
        },
    });

    const streamContext = getStreamContext();

    if (streamContext) {
      return new Response(
        await streamContext.resumableStream(streamId, () => stream.pipeThrough(new JsonToSseTransformStream())),
      );
    } else {
      return new Response(stream);
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
