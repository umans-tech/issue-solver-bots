import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/auth';

export async function POST(request: Request) {
  try {
    // Check authentication
    const session = await getServerSession(authOptions) as any;
    if (!session?.user?.id) {
      console.error("Authentication failed: No user ID in session");
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Get the knowledge base ID from the user's session
    const knowledgeBaseId = session?.user?.selectedSpace?.knowledgeBaseId;
    
    if (!knowledgeBaseId) {
      console.log("No repository connected: No knowledge base ID found in session");
      return NextResponse.json({
        success: false,
        message: 'No repository connected'
      });
    }
    
    // Get the CUDU API endpoint from environment variables
    const cuduEndpoint = process.env.CUDU_ENDPOINT;

    if (!cuduEndpoint) {
      return NextResponse.json(
        { error: 'CUDU API endpoint is not configured' },
        { status: 500 }
      );
    }
    
    // Call the repository API endpoint to trigger reindexing
    const apiUrl = `${cuduEndpoint}/repositories/${knowledgeBaseId}`;
    console.log(`Triggering repository sync: ${apiUrl}`);
    
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      console.error(`Error syncing repository: ${response.statusText}`);
      return NextResponse.json(
        { error: 'Failed to sync repository' },
        { status: response.status }
      );
    }
    
    // Get the response data
    const data = await response.json();
    
    // Return success response
    return NextResponse.json({
      success: true,
      message: data.message || 'Repository sync initiated successfully'
    });
  } catch (error) {
    console.error('Error syncing repository:', error);
    return NextResponse.json(
      { error: 'Failed to sync repository' },
      { status: 500 }
    );
  }
} 