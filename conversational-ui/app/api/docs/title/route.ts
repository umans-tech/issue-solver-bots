import { NextResponse } from 'next/server';
import { GetObjectCommand, S3Client } from '@aws-sdk/client-s3';
import { auth } from '@/app/(auth)/auth';

function streamToString(stream: any): Promise<string> {
  return new Promise((resolve, reject) => {
    const chunks: any[] = [];
    stream.on('data', (chunk: any) => chunks.push(Buffer.from(chunk)));
    stream.on('error', (err: any) => reject(err));
    stream.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')));
  });
}

export async function GET(request: Request) {
  try {
    const session = await auth();
    if (!session?.user)
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { searchParams } = new URL(request.url);
    const kbId =
      searchParams.get('kbId') || session.user.selectedSpace?.knowledgeBaseId;
    const commitSha = searchParams.get('commitSha');
    const path = searchParams.get('path');
    if (!kbId || !commitSha || !path) {
      return NextResponse.json(
        { error: 'kbId, commitSha and path are required' },
        { status: 400 },
      );
    }

    const BUCKET_NAME = process.env.BLOB_BUCKET_NAME || '';
    const s3Client = new S3Client({
      region: process.env.BLOB_REGION || '',
      endpoint: process.env.BLOB_ENDPOINT || '',
      forcePathStyle: !!process.env.BLOB_ENDPOINT,
      credentials: {
        accessKeyId: process.env.BLOB_ACCESS_KEY_ID || '',
        secretAccessKey: process.env.BLOB_READ_WRITE_TOKEN || '',
      },
    });

    const key = `base/${kbId}/docs/${commitSha}/${path}`;
    const cmd = new GetObjectCommand({ Bucket: BUCKET_NAME, Key: key });
    const res = await s3Client.send(cmd);
    const bodyString = await streamToString(res.Body);
    const titleMatch = bodyString.match(/^#\s+(.+)$/m);
    const title = titleMatch ? titleMatch[1].trim() : null;
    return NextResponse.json({ title });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch title' },
      { status: 500 },
    );
  }
}
