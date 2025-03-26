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

    // No longer require accessToken - it can be empty for public repos
    // if (!accessToken) {
    //   return NextResponse.json(
    //     { error: 'Access token is required' },
    //     { status: 400 }
    //   );
    // }

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
      access_token: accessToken, // This can now be an empty string for public repos
      user_id: userId || session.user.id,
      space_id: spaceId || '',
    };
    
    console.log("Sending request to CUDU API:", {
      endpoint: `${cuduEndpoint}/repositories`,
      body: { ...requestBody, access_token: accessToken ? '***REDACTED***' : '(empty - public repo)' }
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

    // Ensure processId and knowledgeBaseId are always clear in the response
    // In production code, we want to use the actual data from the CUDU API
    const responseData = {
      ...data,
      // Ensure process_id and knowledge_base_id are available
      process_id: data.process_id,
      knowledge_base_id: data.knowledge_base_id
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