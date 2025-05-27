import { NextResponse } from 'next/server';
import { getServerSession } from 'next-auth/next';
import { authOptions } from '@/auth';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ processId: string }> }
) {
  // Use a try-catch to handle any errors
  try {
    // Extract processId from params
    const { processId } = await params;
    
    if (!processId) {
      return NextResponse.json(
        { error: 'Process ID is required' },
        { status: 400 }
      );
    }
    
    console.log(`Getting status for process: ${processId}`);
    
    // Check authentication
    const session = await getServerSession(authOptions) as any;
    if (!session?.user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }
    
    // Get the CUDU API endpoint from environment variables
    const cuduEndpoint = process.env.CUDU_ENDPOINT;
    
    if (!cuduEndpoint) {
      console.error("CUDU API endpoint is not configured");
      return NextResponse.json(
        { error: 'CUDU API endpoint is not configured' },
        { status: 500 }
      );
    }
    
    // Forward the request to the CUDU API
    const apiUrl = `${cuduEndpoint}/processes/${processId}`;
    console.log(`Fetching process status from: ${apiUrl}`);
    
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Log the response status
    console.log(`CUDU API response status: ${response.status}`);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error(`Error fetching process status: ${response.statusText}`, errorData);
      
      return NextResponse.json(
        { error: 'Failed to fetch process status', details: errorData },
        { status: response.status }
      );
    }
    
    // Get the response data
    const data = await response.json();
    console.log("Process status data from CUDU:", data);
    
    // Enhance the response by ensuring 'status' field is clearly set
    let enhancedResponse = { ...data };

    // If status is not directly present, try to extract it from events
    if (!enhancedResponse.status && enhancedResponse.events && enhancedResponse.events.length > 0) {
      const latestEvent = enhancedResponse.events[0]; // Assuming events are sorted with newest first
      
      // Try to extract status from event type
      if (latestEvent.type) {
        // Convert event_type to a status (e.g., "repository_connected" -> "connected")
        const eventType = latestEvent.type.toLowerCase();
        console.log(`Extracting status from event type: ${eventType}`);
        
        if (eventType.includes('connect')) {
          enhancedResponse.status = 'connected';
        } else if (eventType.includes('index')) {
          enhancedResponse.status = 'indexed';
        } else if (eventType.includes('fail')) {
          enhancedResponse.status = 'failed';
        }
        
        console.log(`Derived status from event type: ${enhancedResponse.status}`);
      }
    }

    console.log("Enhanced response:", {
      id: enhancedResponse.id,
      status: enhancedResponse.status,
      // Include other relevant fields but not the full events array
    });

    // Return the process status with enhancements
    return NextResponse.json(enhancedResponse);
  } catch (error) {
    console.error('Error fetching process status:', error);
    
    return NextResponse.json(
      { error: 'Failed to fetch process status' },
      { status: 500 }
    );
  }
} 