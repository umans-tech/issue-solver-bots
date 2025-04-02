import { NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';

export async function GET(request: Request) {
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

    // Get the process ID from the user's session
    const processId = session?.user?.selectedSpace?.processId;
    
    if (!processId) {
      console.log("No repository connected: No process ID found in session");
      return NextResponse.json({
        connected: false,
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
    
    // Call the process API endpoint to get repository details
    const apiUrl = `${cuduEndpoint}/processes/${processId}`;
    console.log(`Fetching repository details from process: ${apiUrl}`);
    
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    if (!response.ok) {
      console.error(`Error fetching repository details: ${response.statusText}`);
      return NextResponse.json(
        { error: 'Failed to fetch repository details' },
        { status: response.status }
      );
    }
    
    // Get the response data
    const data = await response.json();
    
    // Find the repository_connected event if available
    const repoEvent = data.events?.find((event: { type: string }) => 
      event.type?.toLowerCase() === 'repository_connected');

    // Find the repository_indexed event if available
    const indexedEvent = data.events?.find((event: { type: string }) => 
      event.type?.toLowerCase() === 'repository_indexed');
      
    if (!repoEvent) {
      return NextResponse.json(
        { error: 'Repository connection details not found' },
        { status: 404 }
      );
    }
    
    // Return the repository URL and other details (but mask the access token)
    return NextResponse.json({
      connected: true,
      url: repoEvent.url,
      status: data.status || 'unknown',
      knowledge_base_id: repoEvent.knowledge_base_id,
      process_id: processId,
      // Add Git information if available
      branch: indexedEvent?.branch,
      commit_sha: indexedEvent?.commit_sha,
      // Add indexation timestamps if available
      indexing_started: repoEvent?.occurred_at,
      indexing_completed: indexedEvent?.occurred_at
    });
  } catch (error) {
    console.error('Error retrieving repository details:', error);
    return NextResponse.json(
      { error: 'Failed to retrieve repository details' },
      { status: 500 }
    );
  }
}

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