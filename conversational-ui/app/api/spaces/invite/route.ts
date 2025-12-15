import { NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';
import { getUser, inviteUserToSpace } from '@/lib/db/queries';
import { sendSpaceInviteNotificationEmail } from '@/lib/email';

export async function POST(request: Request) {
  try {
    // Check authentication
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Parse request body
    const { spaceId, email } = await request.json();

    // Validate required fields
    if (!spaceId || !email) {
      return NextResponse.json(
        { error: 'Space ID and email are required' },
        { status: 400 },
      );
    }

    // Get the current user (inviter) for email notification
    const [inviter] = await getUser(session.user.email!);
    if (!inviter) {
      return NextResponse.json({ error: 'Inviter not found' }, { status: 404 });
    }

    // Invite user to space
    const result = await inviteUserToSpace(spaceId, email);

    if (!result.success) {
      return NextResponse.json({ error: result.error }, { status: 400 });
    }

    // Send email notification to the invited user
    try {
      await sendSpaceInviteNotificationEmail(
        result.user?.email,
        result.space?.name,
        inviter.email,
      );
    } catch (emailError) {
      console.error(
        'Failed to send space invite notification email:',
        emailError,
      );
      // Continue without failing the invite if email fails
      // The user was already added to the space successfully
    }

    return NextResponse.json(
      {
        message: 'User invited successfully',
        spaceName: result.space?.name,
        userEmail: result.user?.email,
      },
      { status: 200 },
    );
  } catch (error) {
    console.error('Error inviting user to space:', error);
    return NextResponse.json(
      { error: 'Failed to invite user to space' },
      { status: 500 },
    );
  }
}
