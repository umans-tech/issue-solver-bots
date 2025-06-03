import { NextResponse } from 'next/server';

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const spaceId = searchParams.get('space_id');
    const processType = searchParams.get('process_type');
    const status = searchParams.get('status');
    const limit = searchParams.get('limit') || '50';
    const offset = searchParams.get('offset') || '0';

    // Build query parameters for the backend API
    const queryParams = new URLSearchParams({
      limit,
      offset,
    });

    if (spaceId) queryParams.set('space_id', spaceId);
    if (processType) queryParams.set('process_type', processType);
    if (status) queryParams.set('status', status);

    const backendUrl = process.env.CUDU_ENDPOINT;
    const response = await fetch(`${backendUrl}/processes?${queryParams.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      console.error('Backend response not OK:', response.status, response.statusText);
      return NextResponse.json(
        { error: `Backend service error: ${response.statusText}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    
    // Enhance the response data to ensure consistent field names
    const enhancedProcesses = data.processes?.map((process: any) => ({
      ...process,
      // Ensure consistent status mapping
      status: process.status || 'unknown',
      // Add processType if not present but type is available
      processType: process.processType || process.type,
      // Format dates properly
      createdAt: process.createdAt || process.created_at,
      updatedAt: process.updatedAt || process.updated_at,
    })) || [];

    return NextResponse.json({
      ...data,
      processes: enhancedProcesses,
    });
  } catch (error) {
    console.error('Error fetching processes:', error);
    
    return NextResponse.json(
      { error: 'Failed to fetch processes from backend' },
      { status: 500 }
    );
  }
} 