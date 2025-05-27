import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/auth';
import { getChatsByUserId } from '@/lib/db/queries';

export async function GET() {
  const session = await getServerSession(authOptions) as any;

  if (!session || !session.user) {
    return Response.json('Unauthorized!', { status: 401 });
  }

  // biome-ignore lint: Forbidden non-null assertion.
  const chats = await getChatsByUserId({ id: session.user.id! });
  return Response.json(chats);
}
