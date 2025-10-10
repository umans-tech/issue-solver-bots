import { NextResponse } from 'next/server';

import { auth } from '@/app/(auth)/auth';

const NOTION_OAUTH_START_PATH = '/integrations/notion/oauth/start';

function buildCuduUrl(path: string, search: Record<string, string>) {
  const cuduEndpoint = process.env.CUDU_ENDPOINT;
  if (!cuduEndpoint) {
    throw new Error('CUDU_ENDPOINT is not configured');
  }

  const url = new URL(`${cuduEndpoint}${path}`);
  Object.entries(search).forEach(([key, value]) => url.searchParams.set(key, value));
  return url.toString();
}

export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = (await request.json().catch(() => ({}))) as {
      spaceId?: string;
      returnPath?: string;
    };

    const spaceId = body?.spaceId ?? session.user.selectedSpace?.id;
    if (!spaceId) {
      return NextResponse.json(
        { error: 'No active space selected' },
        { status: 400 },
      );
    }

    const returnPath = body?.returnPath ?? '/integrations/notion/callback';

    const response = await fetch(
      buildCuduUrl(NOTION_OAUTH_START_PATH, {
        space_id: spaceId,
        return_path: returnPath,
      }),
      {
        method: 'GET',
        headers: {
          'X-User-ID': session.user.id,
        },
        cache: 'no-store',
      },
    );

    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      return NextResponse.json(
        { error: payload?.detail || 'Failed to start Notion OAuth flow' },
        { status: response.status },
      );
    }

    return NextResponse.json(payload);
  } catch (error: any) {
    console.error('Failed to start Notion OAuth flow:', error);
    return NextResponse.json(
      { error: 'Failed to start Notion OAuth flow' },
      { status: 500 },
    );
  }
}
