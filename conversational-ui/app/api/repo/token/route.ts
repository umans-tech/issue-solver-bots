import { NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';

export async function PUT(request: Request) {
  try {
    // Check authentication
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Get the knowledge base ID from the user's session
    const knowledgeBaseId = session?.user?.selectedSpace?.knowledgeBaseId;
    
    if (!knowledgeBaseId) {
      return NextResponse.json(
        { error: 'No repository connected' },
        { status: 400 }
      );
    }

    // Parse the request body
    const { accessToken } = await request.json();
    
    if (!accessToken) {
      return NextResponse.json(
        { error: 'Access token is required' },
        { status: 400 }
      );
    }

    // Get the CUDU API endpoint from environment variables
    const cuduEndpoint = process.env.CUDU_ENDPOINT;
    if (!cuduEndpoint) {
      return NextResponse.json(
        { error: 'CUDU API endpoint is not configured' },
        { status: 500 }
      );
    }

    // Call the backend token rotation endpoint
    const apiUrl = `${cuduEndpoint}/repositories/${knowledgeBaseId}/token`;
    const response = await fetch(apiUrl, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': session.user.id,
      },
      body: JSON.stringify({
        access_token: accessToken,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
          return NextResponse.json(
      { error: data.detail || 'Failed to update token' },
      { status: response.status }
    );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Token update error:', error);
    return NextResponse.json(
      { error: 'Failed to update token' },
      { status: 500 }
    );
  }
} 