import { NextResponse } from 'next/server';

import { auth } from '@/app/(auth)/auth';

const NOTION_PATH = '/integrations/notion';

function buildCuduUrl(path: string) {
  const cuduEndpoint = process.env.CUDU_ENDPOINT;
  if (!cuduEndpoint) {
    throw new Error('CUDU_ENDPOINT is not configured');
  }
  return `${cuduEndpoint}${path}`;
}

export async function GET(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const spaceId = searchParams.get('spaceId') || session.user.selectedSpace?.id;

    if (!spaceId) {
      return NextResponse.json({ connected: false });
    }

    const apiUrl = buildCuduUrl(`${NOTION_PATH}/${spaceId}`);
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': session.user.id,
      },
      cache: 'no-store',
    });

    if (response.status === 404) {
      return NextResponse.json({ connected: false });
    }

    if (!response.ok) {
      const detail = await response.text();
      return NextResponse.json(
        { error: detail || 'Failed to fetch Notion integration' },
        { status: response.status },
      );
    }

    const data = await response.json();
    return NextResponse.json({ connected: true, integration: data });
  } catch (error: any) {
    console.error('Failed to load Notion integration:', error);
    return NextResponse.json(
      { error: 'Failed to load Notion integration' },
      { status: 500 },
    );
  }
}

export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const accessToken: string | undefined = body?.accessToken;
    const spaceId: string | undefined =
      body?.spaceId || session.user.selectedSpace?.id;

    if (!accessToken) {
      return NextResponse.json(
        { error: 'Notion access token is required' },
        { status: 400 },
      );
    }

    if (!spaceId) {
      return NextResponse.json(
        { error: 'No active space selected' },
        { status: 400 },
      );
    }

    const response = await fetch(buildCuduUrl(NOTION_PATH), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': session.user.id,
      },
      cache: 'no-store',
      body: JSON.stringify({
        access_token: accessToken,
        space_id: spaceId,
      }),
    });

    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      return NextResponse.json(
        { error: payload?.detail || 'Failed to connect Notion' },
        { status: response.status },
      );
    }

    return NextResponse.json(payload, { status: 201 });
  } catch (error: any) {
    console.error('Failed to connect Notion:', error);
    return NextResponse.json(
      { error: 'Failed to connect Notion' },
      { status: 500 },
    );
  }
}

export async function PUT(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const accessToken: string | undefined = body?.accessToken;
    const spaceId: string | undefined =
      body?.spaceId || session.user.selectedSpace?.id;

    if (!accessToken) {
      return NextResponse.json(
        { error: 'Notion access token is required' },
        { status: 400 },
      );
    }

    if (!spaceId) {
      return NextResponse.json(
        { error: 'No active space selected' },
        { status: 400 },
      );
    }

    const response = await fetch(buildCuduUrl(`${NOTION_PATH}/${spaceId}/token`), {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': session.user.id,
      },
      cache: 'no-store',
      body: JSON.stringify({ access_token: accessToken }),
    });

    const payload = await response.json().catch(() => ({}));

    if (!response.ok) {
      return NextResponse.json(
        { error: payload?.detail || 'Failed to rotate Notion token' },
        { status: response.status },
      );
    }

    return NextResponse.json(payload, { status: 200 });
  } catch (error: any) {
    console.error('Failed to rotate Notion token:', error);
    return NextResponse.json(
      { error: 'Failed to rotate Notion token' },
      { status: 500 },
    );
  }
}
