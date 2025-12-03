import { NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';
import { getCachedProcess, setCachedProcess } from '@/lib/process-cache';

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
    const cached = getCachedProcess(processId);
    let data: any;
    if (cached) {
      console.log(`Using cached process snapshot for repository details: ${processId}`);
      data = cached;
    } else {
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
      
      data = await response.json();
      setCachedProcess(processId, data);
    }
    
    // Find the repository_connected event if available
    const repoEvent = data.events?.find((event: { type: string }) => 
      event.type?.toLowerCase() === 'repository_connected');

    // Find latest (by occurred_at) repository_integration_failed event if available
    const connectionFailedEvent = data.events
      ?.filter((event: { type: string; occurred_at: string }) => 
        event.type?.toLowerCase() === 'repository_integration_failed')
      .sort((a: { occurred_at: string }, b: { occurred_at: string }) => 
        new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime())[0];
      
    // Find latest (by occurred_at) indexation requested event if available
    const latestIndexationRequestedEvent = data.events
      ?.filter((event: { type: string; occurred_at: string }) => 
        event.type?.toLowerCase() === 'repository_indexation_requested')
      .sort((a: { occurred_at: string }, b: { occurred_at: string }) => 
        new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime())[0];

    // Find latest (by occurred_at) repository_indexed event if available
    const latestRepositoryIndexedEvent = data.events
      ?.filter((event: { type: string; occurred_at: string }) => 
        event.type?.toLowerCase() === 'repository_indexed')
      .sort((a: { occurred_at: string }, b: { occurred_at: string }) => 
        new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime())[0];
      
    const failedEventTime = connectionFailedEvent
      ? new Date(connectionFailedEvent.occurred_at).getTime()
      : 0;
    const lastSuccessTime = latestRepositoryIndexedEvent 
      ? new Date(latestRepositoryIndexedEvent.occurred_at).getTime()
      : 0;
    const failureWithoutSuccess = connectionFailedEvent && !latestRepositoryIndexedEvent;
    const failureAfterSuccess = connectionFailedEvent && latestRepositoryIndexedEvent && failedEventTime > lastSuccessTime;

    // If we have a failure and no success yet, keep the hard error flow
    if (failureWithoutSuccess) {
      console.log(`Repository connection failed: ${connectionFailedEvent.error_message}`);
      return NextResponse.json({
        connected: false,
        error: true,
        errorType: connectionFailedEvent.error_type,
        errorMessage: connectionFailedEvent.error_message,
        url: connectionFailedEvent.url,
        status: 'failed',
        process_id: processId
      });
    }
      
    if (!repoEvent) {
      return NextResponse.json(
        { error: 'Repository connection details not found' },
        { status: 404 }
      );
    }
    
    // Determine the indexing start time: use the latest indexation requested event if available,
    // otherwise use the repository connected event
    const indexingStartTime = latestIndexationRequestedEvent?.occurred_at || repoEvent.occurred_at;
    
    // Get the most recent token permissions (from either initial connection or token rotation)
    const tokenRotatedEvents = data.events.filter((e: any) => e.type === 'repository_token_rotated');
    let mostRecentTokenPermissions = repoEvent.token_permissions;
    
    if (tokenRotatedEvents.length > 0) {
      // Find the most recent token rotation event
      const mostRecentTokenRotation = tokenRotatedEvents.reduce((latest: any, current: any) => {
        return new Date(current.occurred_at) > new Date(latest.occurred_at) ? current : latest;
      });
      
      // If the token rotation is more recent than the original connection, use its permissions
      if (new Date(mostRecentTokenRotation.occurred_at) > new Date(repoEvent.occurred_at)) {
        mostRecentTokenPermissions = mostRecentTokenRotation.token_permissions || mostRecentTokenPermissions;
      }
    }

    // Return the repository URL and other details (but mask the access token)
    return NextResponse.json({
      connected: true,
      url: repoEvent.url,
      status: failureAfterSuccess ? 'failed' : data.status || 'unknown',
      knowledge_base_id: repoEvent.knowledge_base_id,
      process_id: processId,
      branch: latestRepositoryIndexedEvent?.branch,
      commit_sha: latestRepositoryIndexedEvent?.commit_sha,
      indexing_started: indexingStartTime,
      indexing_completed: latestRepositoryIndexedEvent?.occurred_at,
      last_failed_at: connectionFailedEvent?.occurred_at,
      last_failed_error: connectionFailedEvent?.error_message,
      last_failed_type: connectionFailedEvent?.error_type,
      token_permissions: mostRecentTokenPermissions
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
      space_id: spaceId || '',
    };
    
    console.log("Sending request to CUDU API:", {
      endpoint: `${cuduEndpoint}/repositories`,
      body: { ...requestBody, access_token: '***REDACTED***' },
      headers: { 'X-User-ID': userId || session.user.id }
    });

    // Forward the request to the CUDU API with user and space information
    const response = await fetch(`${cuduEndpoint}/repositories`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': userId || session.user.id,
      },
      body: JSON.stringify(requestBody),
    });

    // Log the response status
    console.log(`CUDU API response status: ${response.status}`);
    
    // Handle error responses from the backend with specific error messages
    if (!response.ok) {
      const data = await response.json();
      const errorDetail = data.detail || 'Unknown error';
      console.error(`Error from CUDU API: ${errorDetail}`);
      
      // Map backend error status codes to appropriate error types and messages
      let errorMessage = errorDetail;
      let errorType = 'unknown';
      
      switch (response.status) {
        case 401:
          errorType = 'authentication_failed';
          errorMessage = 'Authentication failed. Please check your access token.';
          break;
        case 403:
          errorType = 'permission_denied';
          errorMessage = 'Permission denied. Please check your access rights to this repository.';
          break;
        case 404:
          errorType = 'repository_not_found';
          errorMessage = 'Repository not found. Please check the URL.';
          break;
        case 502:
          errorType = 'repository_unavailable';
          errorMessage = 'Could not access the repository. Please check the URL and your internet connection.';
          break;
        default:
          errorType = 'unexpected_error';
          errorMessage = `Error connecting to repository: ${errorDetail}`;
      }
      
      return NextResponse.json(
        { 
          error: errorMessage,
          errorType,
          errorMessage,
          success: false
        }, 
        { status: response.status }
      );
    }
    
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
    console.error("Error in repository connection:", error);
    return NextResponse.json(
      { 
        error: 'Failed to connect repository',
        errorType: 'unexpected_error',
        errorMessage: 'An unexpected error occurred while trying to connect to the repository.'
      },
      { status: 500 }
    );
  }
} 
