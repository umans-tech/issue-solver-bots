import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const { repoUrl, accessToken } = await request.json();

    // Validate input
    if (!repoUrl) {
      return NextResponse.json(
        { error: 'Repository URL is required' },
        { status: 400 }
      );
    }

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

    // Forward the request to the CUDU API
    const response = await fetch(`${cuduEndpoint}/repositories`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: repoUrl,
        accessToken,
      }),
    });

    // Get the response data
    const data = await response.json();

    // Return the response from the CUDU API
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error connecting repository:', error);
    return NextResponse.json(
      { error: 'Failed to connect repository' },
      { status: 500 }
    );
  }
} 