import { NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';
import { getSpaceMembers, getSpacesForUser } from '@/lib/db/queries';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ spaceId: string }> }
) {
  try {
    // Check authentication
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const { spaceId } = await params;

    // Verify user has access to this space
    const userSpaces = await getSpacesForUser(session.user.id);
    const hasAccess = userSpaces.some(space => space.id === spaceId);

    if (!hasAccess) {
      return NextResponse.json(
        { error: 'Access denied to this space' },
        { status: 403 }
      );
    }

    // Get space members
    const members = await getSpaceMembers(spaceId);

    return NextResponse.json(members, { status: 200 });
  } catch (error) {
    console.error('Error fetching space members:', error);
    return NextResponse.json(
      { error: 'Failed to fetch space members' },
      { status: 500 }
    );
  }
} 