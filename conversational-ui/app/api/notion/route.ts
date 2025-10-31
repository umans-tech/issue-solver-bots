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

export async function POST() {
  return NextResponse.json(
    { error: 'Direct Notion token connection is no longer supported.' },
    { status: 410 },
  );
}

export async function PUT() {
  return NextResponse.json(
    { error: 'Direct Notion token rotation is no longer supported.' },
    { status: 410 },
  );
}
