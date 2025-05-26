import { createDataStream, UIMessage, appendResponseMessages, smoothStream, streamText, } from 'ai';

import { auth } from '@/app/(auth)/auth';
import { myProvider } from '@/lib/ai/models';
import { systemPrompt } from '@/lib/ai/prompts';
import { deleteChatById, getChatById, saveChat, saveMessages, updateChatTitleById, createStreamId, getStreamIdsByChatId } from '@/lib/db/queries';
import { generateUUID, getMostRecentUserMessage, getTrailingMessageId, } from '@/lib/utils';
import { generateTitleFromUserMessage } from '../../actions';
import { createDocument } from '@/lib/ai/tools/create-document';
import { updateDocument } from '@/lib/ai/tools/update-document';
import { requestSuggestions } from '@/lib/ai/tools/request-suggestions';
import { getWeather } from '@/lib/ai/tools/get-weather';
import { codebaseAssistant } from '@/lib/ai/tools/codebase-assistant';
import { codebaseSearch } from '@/lib/ai/tools/codebase-search';
import { webSearch } from '@/lib/ai/tools/web_search';
import { remoteCodingAgent } from '@/lib/ai/tools/remote-coding-agent';
import { Chat } from '@/lib/db/schema';
import { createResumableStreamContext, type ResumableStreamContext } from 'resumable-stream';
import { after } from 'next/server';

export const maxDuration = 60;
const maxSteps = 40;
const maxRetries = 10;

let globalStreamContext: ResumableStreamContext | null = null;

function getStreamContext() {
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
        messages: Array<UIMessage>;
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
        await saveChat({ id, userId: session.user.id, title });
    }

    await saveMessages({
        messages: [
            {
              chatId: id,
              id: userMessage.id,
              role: 'user',
              parts: userMessage.parts,
              attachments: userMessage.experimental_attachments ?? [],
              createdAt: new Date(),
            },
          ],
    });

    const streamId = generateUUID();
    await createStreamId({ streamId, chatId: id });
    const stream = createDataStream({
        execute: (dataStream) => {
            const result = streamText({
                model: myProvider.languageModel(selectedChatModel),
                system: systemPrompt({ selectedChatModel }),
                messages,
                maxSteps: maxSteps,
                maxRetries: maxRetries,
                experimental_activeTools: [
                    'getWeather',
                    'createDocument',
                    'updateDocument',
                    'requestSuggestions',
                    'codebaseAssistant',
                    'codebaseSearch',
                    'webSearch',
                    'remoteCodingAgent',
                ],
                experimental_transform: smoothStream({ chunking: 'word' }),
                experimental_generateMessageId: generateUUID,
                tools: {
                    getWeather,
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
                    webSearch: webSearch,
                    remoteCodingAgent: remoteCodingAgent({
                        session: Object.assign({}, session, { knowledgeBaseId }),
                        dataStream,
                    }),
                },
                onFinish: async ({ response }) => {
                    if (session.user?.id) {
                        try {
                            const assistantId = getTrailingMessageId({
                                messages: response.messages.filter(
                                  (message) => message.role === 'assistant',
                                ),
                              });
              
                              if (!assistantId) {
                                throw new Error('No assistant message found!');
                              }
              
                              const [, assistantMessage] = appendResponseMessages({
                                messages: [userMessage],
                                responseMessages: response.messages,
                            });

                            await saveMessages({
                                messages: [
                                    {
                                      id: assistantId,
                                      chatId: id,
                                      role: assistantMessage.role,
                                      parts: assistantMessage.parts,
                                      attachments:
                                        assistantMessage.experimental_attachments ?? [],
                                      createdAt: new Date(),
                                    },
                                ],
                            });
                        } catch (error) {
                            console.error('Failed to save chat');
                        }
                    }
                },
                experimental_telemetry: {
                    isEnabled: true,
                    functionId: 'stream-text',
                },
            });

            result.consumeStream();

            result.mergeIntoDataStream(dataStream, {
                sendReasoning: true,
            });
        },
        onError: () => {
            return 'Oops, an error occured!';
        },
    });

    const streamContext = getStreamContext();

    if (streamContext) {
      return new Response(
        await streamContext.resumableStream(streamId, () => stream),
      );
    } else {
      return new Response(stream);
    }
}

export async function GET(request: Request) {
    const streamContext = getStreamContext();

    if (!streamContext) {
      return new Response(null, { status: 204 });
    }
  
    const { searchParams } = new URL(request.url);
    const chatId = searchParams.get('chatId');
  
    if (!chatId) {
      return new Response('id is required', { status: 400 });
    }
  
    const session = await auth();
  
    let chat: Chat;
    
    try {
      chat = await getChatById({ id: chatId });
    } catch {
      return new Response('Not found', { status: 404 });
    }
    
    if (!chat) {    
      return new Response('Not found', { status: 404 });
    }
    
    if (chat.visibility !== 'public' && !session?.user) {
      return new Response('Unauthorized', { status: 401 });
    }
  
    if (chat.visibility === 'private' && chat.userId !== session?.user.id) {
      return new Response('Forbidden', { status: 403 });
    }
  
    const streamIds = await getStreamIdsByChatId({ chatId });
  
    if (!streamIds.length) {
      return new Response('No streams found', { status: 404 });
    }
  
    const recentStreamId = streamIds.at(-1);
  
    if (!recentStreamId) {
      return new Response('No recent stream found', { status: 404 });
    }
  
    const emptyDataStream = createDataStream({
      execute: () => {},
    });
  
    return new Response(
      await streamContext.resumableStream(recentStreamId, () => emptyDataStream),
      {
        status: 200,
      },
    );
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
