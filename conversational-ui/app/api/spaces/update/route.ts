import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/auth';
import { updateSpace } from '@/lib/db/queries';

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
    const { spaceId, knowledgeBaseId, processId, name, isDefault } = await request.json();

    // Validate required fields
    if (!spaceId) {
      return NextResponse.json(
        { error: 'Space ID is required' },
        { status: 400 }
      );
    }

    // Build update object with provided fields
    const updates: {
      knowledgeBaseId?: string;
      processId?: string;
      name?: string;
      isDefault?: boolean;
    } = {};

    if (knowledgeBaseId !== undefined) updates.knowledgeBaseId = knowledgeBaseId;
    if (processId !== undefined) updates.processId = processId;
    if (name !== undefined) updates.name = name;
    if (isDefault !== undefined) updates.isDefault = isDefault;

    // Update space in the database
    const updatedSpace = await updateSpace(spaceId, updates);

    if (!updatedSpace) {
      return NextResponse.json(
        { error: 'Failed to update space' },
        { status: 500 }
      );
    }

    // Return success with updated space data and clear information about the changes
    return NextResponse.json({
      ...updatedSpace,
      // Include information about what was updated for clarity
      updates: {
        knowledgeBaseId: updates.knowledgeBaseId !== undefined ? 'updated' : 'unchanged',
        processId: updates.processId !== undefined ? 'updated' : 'unchanged',
        name: updates.name !== undefined ? 'updated' : 'unchanged',
        isDefault: updates.isDefault !== undefined ? 'updated' : 'unchanged',
      }
    }, { status: 200 });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to update space' },
      { status: 500 }
    );
  }
} 