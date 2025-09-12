import { NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';

export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { knowledgeBaseId, global, project, script } = await request.json();

    if (!knowledgeBaseId) {
      return NextResponse.json({ error: 'knowledgeBaseId is required' }, { status: 400 });
    }

    const cuduEndpoint = process.env.CUDU_ENDPOINT;
    if (!cuduEndpoint) {
      return NextResponse.json({ error: 'CUDU API endpoint is not configured' }, { status: 500 });
    }

    const payload: Record<string, string> = {};
    if (typeof global === 'string' && global.trim()) payload.global = global.trim();
    if (typeof project === 'string' && project.trim()) payload.project = project.trim();
    if (!payload.global && !payload.project && typeof script === 'string' && script.trim()) {
      payload.script = script.trim();
    }

    if (!payload.global && !payload.project && !payload.script) {
      return NextResponse.json({ error: 'Provide global/project or script' }, { status: 400 });
    }

    const apiUrl = `${cuduEndpoint}/repositories/${knowledgeBaseId}/environments`;

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': session.user.id,
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to setup environment' }, { status: 500 });
  }
}

export async function GET(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const knowledgeBaseId = searchParams.get('knowledgeBaseId');
    if (!knowledgeBaseId) {
      return NextResponse.json({ error: 'knowledgeBaseId is required' }, { status: 400 });
    }

    const cuduEndpoint = process.env.CUDU_ENDPOINT;
    if (!cuduEndpoint) {
      return NextResponse.json({ error: 'CUDU API endpoint is not configured' }, { status: 500 });
    }

    const apiUrl = `${cuduEndpoint}/repositories/${knowledgeBaseId}/environments/latest`;
    const response = await fetch(apiUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': session.user.id,
      },
    });

    const data = await response.json();
    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    return NextResponse.json({ error: 'Failed to get environment' }, { status: 500 });
  }
}


