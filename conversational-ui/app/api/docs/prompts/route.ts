import { NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';

function sanitizeDocsPrompts(input: unknown): Record<string, string> | null {
  if (!input || typeof input !== 'object') {
    return null;
  }
  const entries = Object.entries(input as Record<string, unknown>).reduce<Record<string, string>>((acc, [key, value]) => {
    if (typeof key !== 'string') return acc;
    if (typeof value === 'string') {
      acc[key] = value;
    }
    return acc;
  }, {});
  return Object.keys(entries).length > 0 ? entries : null;
}

export async function GET(request: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const knowledgeBaseId = searchParams.get('knowledgeBaseId') ?? searchParams.get('kbId');
  if (!knowledgeBaseId) {
    return NextResponse.json({ error: 'knowledgeBaseId is required' }, { status: 400 });
  }

  const cuduEndpoint = process.env.CUDU_ENDPOINT;
  if (!cuduEndpoint) {
    return NextResponse.json({ error: 'CUDU API endpoint is not configured' }, { status: 500 });
  }

  const apiUrl = `${cuduEndpoint}/repositories/${knowledgeBaseId}/auto-documentation`;
  const response = await fetch(apiUrl, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': session.user.id,
    },
  });

  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}

export async function POST(request: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await request.json();
  const knowledgeBaseId: string | undefined = body?.knowledgeBaseId;
  const docsPrompts = sanitizeDocsPrompts(body?.docsPrompts);

  if (!knowledgeBaseId) {
    return NextResponse.json({ error: 'knowledgeBaseId is required' }, { status: 400 });
  }

  if (!docsPrompts) {
    return NextResponse.json({ error: 'docsPrompts must include at least one entry' }, { status: 400 });
  }

  const cuduEndpoint = process.env.CUDU_ENDPOINT;
  if (!cuduEndpoint) {
    return NextResponse.json({ error: 'CUDU API endpoint is not configured' }, { status: 500 });
  }

  const apiUrl = `${cuduEndpoint}/repositories/${knowledgeBaseId}/auto-documentation`;
  const response = await fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': session.user.id,
    },
    body: JSON.stringify({ docsPrompts }),
  });

  const data = await response.json();
  return NextResponse.json(data, { status: response.status });
}
