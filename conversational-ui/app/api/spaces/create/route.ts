import { NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';
import { createSpace, setSelectedSpace } from '@/lib/db/queries';

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
    const { name, knowledgeBaseId, processId, isDefault } = await request.json();

    // Validate required fields
    if (!name) {
      return NextResponse.json(
        { error: 'Space name is required' },
        { status: 400 }
      );
    }

    // Create the new space
    const newSpace = await createSpace(
      name,
      session.user.id,
      knowledgeBaseId,
      processId,
      isDefault
    );

    if (!newSpace) {
      return NextResponse.json(
        { error: 'Failed to create space' },
        { status: 500 }
      );
    }

    // Set this as the selected space
    await setSelectedSpace(session.user.id, newSpace.id);

    // Return the created space
    return NextResponse.json(newSpace, { status: 201 });
  } catch (error) {
    console.error('Error creating space:', error);
    return NextResponse.json(
      { error: 'Failed to create space' },
      { status: 500 }
    );
  }
} 