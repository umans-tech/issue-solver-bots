import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/auth';
import { getSpacesForUser } from '@/lib/db/queries';

export async function GET() {
  try {
    // Check authentication
    const session = await getServerSession(authOptions) as any;
    if (!session?.user?.id) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    console.log('Fetching spaces for user:', session.user.id);
    
    // Get all spaces for the user
    const spaces = await getSpacesForUser(session.user.id);
    
    console.log('Found spaces:', spaces);

    // Return the spaces
    return NextResponse.json(spaces, { status: 200 });
  } catch (error) {
    console.error('Error fetching spaces:', error);
    return NextResponse.json(
      { error: 'Failed to fetch spaces' },
      { status: 500 }
    );
  }
} 