import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';
import { getChatById } from '@/lib/db/queries';

export async function POST(req: NextRequest) {
  try {
    const session = await auth();
    if (!session || !session.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { chatId, spaceId } = await req.json();
    
    if (!chatId || !spaceId) {
      return NextResponse.json(
        { error: 'Missing required parameters' },
        { status: 400 }
      );
    }

    // Get the chat
    const chat = await getChatById({ id: chatId });
    if (!chat) {
      return NextResponse.json(
        { error: 'Chat not found' },
        { status: 404 }
      );
    }

    // Check if the user owns the chat
    if (chat.userId !== session.user.id) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 403 }
      );
    }

    // Check if the chat belongs to the specified space
    const belongsToSpace = chat.spaceId === spaceId;
    
    return NextResponse.json({ belongsToSpace });
  } catch (error) {
    console.error('Error checking chat space:', error);
    return NextResponse.json(
      { error: 'Failed to check chat space' },
      { status: 500 }
    );
  }
} 