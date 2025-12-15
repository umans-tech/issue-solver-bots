import { type NextRequest, NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';
import { generateUUID } from '@/lib/utils';
import {
  getChatById,
  getCurrentUserSpace,
  getMessagesByChatId,
  saveChat,
  saveMessages,
} from '@/lib/db/queries';

export async function POST(req: NextRequest) {
  try {
    const session = await auth();
    if (!session || !session.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { sourceChatId } = await req.json();

    if (!sourceChatId) {
      return NextResponse.json(
        { error: 'Missing required parameters' },
        { status: 400 },
      );
    }

    // Get the source chat to get its title
    const sourceChat = await getChatById({ id: sourceChatId });
    if (!sourceChat) {
      return NextResponse.json(
        { error: 'Source chat not found' },
        { status: 404 },
      );
    }

    // Get all messages from the source chat
    const sourceMessages = await getMessagesByChatId({ id: sourceChatId });

    // Create a new chat with the title based on the source chat's title
    const newChatId = generateUUID();

    // Get current user's selected space
    const currentSpace = await getCurrentUserSpace(session.user.id);
    if (!currentSpace) {
      throw new Error('Unable to determine user space');
    }

    await saveChat({
      id: newChatId,
      userId: session.user.id,
      title: `Clone of: ${sourceChat.title}`,
      spaceId: currentSpace.id,
    });

    // Copy all messages
    // Prepare messages for the new chat
    const newMessages = sourceMessages.map((msg) => ({
      id: generateUUID(),
      chatId: newChatId,
      role: msg.role,
      parts: msg.parts,
      attachments: msg.attachments,
      createdAt: new Date(),
    }));

    // Save the copied messages to the new chat
    await saveMessages({ messages: newMessages });

    return NextResponse.json({
      success: true,
      newChatId,
    });
  } catch (error) {
    console.error('Error cloning conversation:', error);
    return NextResponse.json(
      { error: 'Failed to clone conversation' },
      { status: 500 },
    );
  }
}
