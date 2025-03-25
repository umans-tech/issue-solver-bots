import { NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';
import { getSelectedSpace } from '@/lib/db/queries';

// Create a custom route to get the latest session data with fresh space info
export async function GET() {
  try {
    // Get the current session
    const session = await auth();
    
    // If there's no session, return unauthorized
    if (!session) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }
    
    // If we have a session with a user ID, get the latest space data
    if (session?.user?.id) {
      // Get the latest space data directly from the database
      const latestSpace = await getSelectedSpace(session.user.id);
      
      if (latestSpace) {
        console.log("API session refresh: Getting latest space data from database:", {
          id: latestSpace.id,
          knowledgeBaseId: latestSpace.knowledgeBaseId,
          processId: latestSpace.processId
        });
        
        // Create a refreshed session with the latest space data
        const refreshedSession = {
          ...session,
          user: {
            ...session.user,
            selectedSpace: {
              id: latestSpace.id,
              name: latestSpace.name,
              knowledgeBaseId: latestSpace.knowledgeBaseId,
              processId: latestSpace.processId,
              isDefault: latestSpace.isDefault,
            },
          },
        };
        
        // Return the session with the latest data
        return NextResponse.json(refreshedSession);
      }
    }
    
    // If no selected space found, return the original session
    return NextResponse.json(session);
  } catch (error) {
    console.error('Error refreshing session:', error);
    return NextResponse.json(
      { error: 'Failed to refresh session' },
      { status: 500 }
    );
  }
}

// Add POST method to allow client-side session updates
export async function POST() {
  // Simply redirect to GET method for now, since we want the same refresh logic
  return GET();
} 