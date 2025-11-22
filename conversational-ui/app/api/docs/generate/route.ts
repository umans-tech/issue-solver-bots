import { NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';

type Mode = 'update' | 'complete';

export async function POST(request: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const body = await request.json();
  const knowledgeBaseId: string | undefined = body?.knowledgeBaseId || body?.kbId;
  const promptId: string | undefined = body?.promptId || body?.prompt_id;
  const mode: Mode = body?.mode === 'complete' ? 'complete' : 'update';

  if (!knowledgeBaseId) {
    return NextResponse.json({ error: 'knowledgeBaseId is required' }, { status: 400 });
  }
  if (!promptId) {
    return NextResponse.json({ error: 'promptId is required' }, { status: 400 });
  }

  const cuduEndpoint = process.env.CUDU_ENDPOINT;
  if (!cuduEndpoint) {
    return NextResponse.json({ error: 'CUDU API endpoint is not configured' }, { status: 500 });
  }

  const apiUrl = `${cuduEndpoint}/repositories/${knowledgeBaseId}/auto-documentation/generate`;
  const response = await fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-User-ID': session.user.id,
    },
    body: JSON.stringify({ promptId, mode }),
  });

  const payload = await response.json();
  return NextResponse.json(payload, { status: response.status });
}
