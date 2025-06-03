import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';
import { generateUUID } from '@/lib/utils';
import { saveChat, getMessagesByChatId, saveMessages, getChatById, getCurrentUserSpace } from '@/lib/db/queries';

export async function POST(req: NextRequest) {
  try {
    const session = await auth();
    if (!session || !session.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { sourceChatId, messageId } = await req.json();
    
    if (!sourceChatId || !messageId) {
      return NextResponse.json(
        { error: 'Missing required parameters' },
        { status: 400 }
      );
    }

    // Get the source chat to get its title
    const sourceChat = await getChatById({ id: sourceChatId });
    if (!sourceChat) {
      return NextResponse.json(
        { error: 'Source chat not found' },
        { status: 404 }
      );
    }

    // Get all messages from the source chat
    const sourceMessages = await getMessagesByChatId({ id: sourceChatId });
    
    // Find the index of the message to branch from
    const branchIndex = sourceMessages.findIndex(msg => msg.id === messageId);
    
    if (branchIndex === -1) {
      return NextResponse.json(
        { error: 'Message not found' },
        { status: 404 }
      );
    }
    
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
      title: `Branch from: ${sourceChat.title}`,
      spaceId: currentSpace.id,
    });
    
    // Copy messages up to the branch point
    const messagesToCopy = sourceMessages.slice(0, branchIndex + 1);
    
    // Prepare messages for the new chat
    const newMessages = messagesToCopy.map(msg => ({
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
      newChatId 
    });
  } catch (error) {
    console.error('Error branching conversation:', error);
    return NextResponse.json(
      { error: 'Failed to branch conversation' },
      { status: 500 }
    );
  }
} 