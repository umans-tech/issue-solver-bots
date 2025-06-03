import { auth } from '@/app/(auth)/auth';
import { getCurrentUserSpace, getChatsByUserIdAndSpaceId } from '@/lib/db/queries';

export async function GET() {
  const session = await auth();

  if (!session || !session.user) {
    return Response.json('Unauthorized!', { status: 401 });
  }

  // Get user's current space
  const currentSpace = await getCurrentUserSpace(session.user.id);
  if (!currentSpace) {
    return Response.json('No space found for user', { status: 500 });
  }

  // Get chats filtered by current space
  const chats = await getChatsByUserIdAndSpaceId({ 
    userId: session.user.id, 
    spaceId: currentSpace.id 
  });
  
  return Response.json(chats);
}
