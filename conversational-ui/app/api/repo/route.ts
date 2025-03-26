import { NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';

export async function POST(request: Request) {
  try {
    // Check authentication
    const session = await auth();
    if (!session?.user?.id) {
      console.error("Authentication failed: No user ID in session");
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const { repoUrl, accessToken, userId, spaceId } = await request.json();
    // Validate input
    if (!repoUrl) {
      return NextResponse.json(
        { error: 'Repository URL is required' },
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

    const requestBody = {
      url: repoUrl,
      access_token: accessToken,
      user_id: userId || session.user.id,
      space_id: spaceId || '',
    };
    
    console.log("Sending request to CUDU API:", {
      endpoint: `${cuduEndpoint}/repositories`,
      body: { ...requestBody, access_token: '***REDACTED***' }
    });

    // Forward the request to the CUDU API with user and space information
    const response = await fetch(`${cuduEndpoint}/repositories`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    // Log the response status
    console.log(`CUDU API response status: ${response.status}`);
    
    // Get the response data
    const data = await response.json();
    console.log("CUDU API response data:", data);

    // Ensure both snake_case and camelCase versions of the knowledge base ID are available
    // This ensures compatibility with different parts of the application
    const knowledgeBaseId = data.knowledgeBaseId || data.knowledge_base_id;
    
    const responseData = {
      ...data,
      // Ensure both formats are available
      knowledge_base_id: knowledgeBaseId,
      knowledgeBaseId: knowledgeBaseId,
      // Ensure process_id is available
      process_id: data.process_id || data.processId,
      processId: data.processId || data.process_id
    };

    // Return the response from the CUDU API with clearer handling of the IDs
    return NextResponse.json(responseData, { status: response.status });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to connect repository' },
      { status: 500 }
    );
  }
} 