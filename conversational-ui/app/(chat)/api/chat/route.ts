import { createDataStreamResponse, createStreamableValue, type Message, smoothStream, streamText, } from 'ai';

import { auth } from '@/app/(auth)/auth';
import { myProvider } from '@/lib/ai/models';
import { systemPrompt } from '@/lib/ai/prompts';
import { deleteChatById, getChatById, saveChat, saveMessages, updateChatTitleById, } from '@/lib/db/queries';
import { generateUUID, getMostRecentUserMessage, sanitizeResponseMessages, } from '@/lib/utils';
import { createResumableStreamConsumer, createResumableStreamPublisher, getLatestStreamId } from '@/lib/resumable-stream';
import { generateTitleFromUserMessage } from '../../actions';
import { createDocument } from '@/lib/ai/tools/create-document';
import { updateDocument } from '@/lib/ai/tools/update-document';
import { requestSuggestions } from '@/lib/ai/tools/request-suggestions';
import { getWeather } from '@/lib/ai/tools/get-weather';
import { codebaseAssistant } from '@/lib/ai/tools/codebase-assistant';
import { codebaseSearch } from '@/lib/ai/tools/codebase-search';
import { webSearch } from '@/lib/ai/tools/web_search';
import { remoteCodingAgent } from '@/lib/ai/tools/remote-coding-agent';
export const maxDuration = 60;
const maxSteps = 40;
const maxRetries = 10;

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const chatId = searchParams.get('chatId');

    // Validate request
    if (!chatId) {
        return new Response('Chat ID is required', { status: 400 });
    }

    const session = await auth();

    if (!session || !session.user || !session.user.id) {
        return new Response('Unauthorized', { status: 401 });
    }

    try {
        // Check if the chat exists and belongs to the user
        const chat = await getChatById({ id: chatId });
        if (!chat || chat.userId !== session.user.id) {
            return new Response('Chat not found or unauthorized', { status: 404 });
        }

        // Get the latest stream ID for this chat
        const streamId = await getLatestStreamId(chatId);
        if (!streamId) {
            return new Response('No active stream found', { status: 404 });
        }

        // Create a consumer for the stream
        const consumer = await createResumableStreamConsumer(streamId);
        if (!consumer) {
            return new Response('Failed to create stream consumer', { status: 500 });
        }

        // Return the resumed stream
        return createDataStreamResponse({
            execute: async (dataStream) => {
                try {
                    const chunks = await consumer.getAllChunks();
                    for (const chunk of chunks) {
                        dataStream.append(chunk);
                    }
                    dataStream.close();
                } catch (error) {
                    console.error('Error resuming stream:', error);
                    dataStream.append({ text: 'Error resuming stream' });
                    dataStream.close();
                }
            },
            onError: () => {
                return 'Error resuming chat stream';
            }
        });
    } catch (error) {
        console.error('Error handling resumed stream request:', error);
        return new Response('Server error', { status: 500 });
    }
}

export async function POST(request: Request) {
    const {
        id,
        messages,
        selectedChatModel,
        knowledgeBaseId,
    }: {
        id: string;
        messages: Array<Message>;
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
        messages: [{ ...userMessage, createdAt: new Date(), chatId: id }],
    });

    // Create a streamable value that can be resumed
    const streamable = createStreamableValue();
    
    // Set up the resumable stream publisher
    const { publisher, streamId } = await createResumableStreamPublisher(id);

    return createDataStreamResponse({
        execute: async (dataStream) => {
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
                onFinish: async ({ response, reasoning }) => {
                    if (session.user?.id) {
                        try {
                            const sanitizedResponseMessages = sanitizeResponseMessages({
                                messages: response.messages,
                                reasoning,
                            });

                            await saveMessages({
                                messages: sanitizedResponseMessages.map((message) => {
                                    return {
                                        id: message.id,
                                        chatId: id,
                                        role: message.role,
                                        content: message.content,
                                        createdAt: new Date(),
                                        experimental_attachments: message.experimental_attachments,
                                    };
                                }),
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

            // Send to both the client and the resumable stream
            if (publisher) {
                result.mergeIntoDataStream({
                    append(chunk) {
                        dataStream.append(chunk);
                        publisher.append(chunk);
                    },
                    close() {
                        dataStream.close();
                        publisher.close();
                    },
                    error(error) {
                        dataStream.error(error);
                        publisher.error(error);
                    }
                }, {
                    sendReasoning: true,
                });
            } else {
                // Fall back to regular streaming if resumable publisher is not available
                result.mergeIntoDataStream(dataStream, {
                    sendReasoning: true,
                });
            }
        },
        onError: () => {
            return 'Oops, an error occured!';
        },
    });
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
