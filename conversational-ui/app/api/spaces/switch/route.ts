import { NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';
import { setSelectedSpace, getSpaceById } from '@/lib/db/queries';

export async function POST(request: Request) {
  try {
    // Check authentication
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Parse request body
    const { spaceId } = await request.json();

    // Validate required fields
    if (!spaceId) {
      return NextResponse.json(
        { error: 'Space ID is required' },
        { status: 400 }
      );
    }

    // Verify the space exists
    const space = await getSpaceById(spaceId);
    if (!space) {
      return NextResponse.json(
        { error: 'Space not found' },
        { status: 404 }
      );
    }

    // Set this as the selected space
    await setSelectedSpace(session.user.id, spaceId);

    // Return the selected space
    return NextResponse.json(space, { status: 200 });
  } catch (error) {
    console.error('Error switching space:', error);
    return NextResponse.json(
      { error: 'Failed to switch space' },
      { status: 500 }
    );
  }
} 