import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/auth';
import { db } from '@/lib/db';
import { spaceToUser } from '@/lib/db/schema';
import { eq, and } from 'drizzle-orm';
import { getUser } from '@/lib/db/queries';

export async function POST(request: Request) {
  try {
    // Check authentication
    const session = await getServerSession(authOptions) as any;
    if (!session?.user?.id) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Parse request body
    const { spaceId, email } = await request.json();

    // Validate required fields
    if (!spaceId || !email) {
      return NextResponse.json(
        { error: 'Space ID and email are required' },
        { status: 400 }
      );
    }

    // Get the user to invite
    const [userToInvite] = await getUser(email);
    if (!userToInvite) {
      return NextResponse.json(
        { error: 'User not found' },
        { status: 404 }
      );
    }

    // Check if the user is already in the space
    const existingMembership = await db
      .select()
      .from(spaceToUser)
      .where(
        and(
          eq(spaceToUser.spaceId, spaceId),
          eq(spaceToUser.userId, userToInvite.id)
        )
      );

    if (existingMembership.length > 0) {
      return NextResponse.json(
        { error: 'User is already a member of this space' },
        { status: 400 }
      );
    }

    // Add the user to the space
    await db.insert(spaceToUser).values({
      spaceId,
      userId: userToInvite.id,
    });

    return NextResponse.json(
      { message: 'User invited successfully' },
      { status: 200 }
    );
  } catch (error) {
    console.error('Error inviting user to space:', error);
    return NextResponse.json(
      { error: 'Failed to invite user to space' },
      { status: 500 }
    );
  }
} 