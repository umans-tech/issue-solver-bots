import { NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';

export async function GET(
  request: Request,
  { params }: { params: Promise<{ processId: string }> },
) {
  try {
    // Extract processId from params
    const { processId } = await params;

    if (!processId) {
      return NextResponse.json(
        { error: 'Process ID is required' },
        { status: 400 },
      );
    }

    console.log(`Getting messages for process: ${processId}`);

    // Check authentication
    const session = await auth();
    if (!session?.user) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Get the CUDU API endpoint from environment variables
    const cuduEndpoint = process.env.CUDU_ENDPOINT;

    if (!cuduEndpoint) {
      console.error('CUDU API endpoint is not configured');
      return NextResponse.json(
        { error: 'CUDU API endpoint is not configured' },
        { status: 500 },
      );
    }

    // Forward the request to the CUDU API
    const apiUrl = `${cuduEndpoint}/processes/${processId}/messages`;
    console.log(`Fetching process messages from: ${apiUrl}`);

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
      console.error(
        `Error fetching process messages: ${response.statusText}`,
        errorData,
      );

      return NextResponse.json(
        { error: 'Failed to fetch process messages', details: errorData },
        { status: response.status },
      );
    }

    // Get the response data
    const data = await response.json();
    console.log(
      `Fetched ${data.length || 0} messages for process ${processId}`,
    );

    // Return the messages
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error fetching process messages:', error);

    return NextResponse.json(
      { error: 'Failed to fetch process messages' },
      { status: 500 },
    );
  }
}
