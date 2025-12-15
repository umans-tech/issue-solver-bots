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

    if (!kbId || !commitSha) {
      return NextResponse.json(
        { error: 'kbId and commitSha are required' },
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

    const key = `base/${kbId}/docs/${commitSha}/index.md`;
    const cmd = new GetObjectCommand({ Bucket: BUCKET_NAME, Key: key });
    const res = await s3Client.send(cmd);
    // @ts-ignore - aws sdk stream type
    const bodyString = await streamToString(res.Body);

    return NextResponse.json({ content: bodyString });
  } catch (error: any) {
    console.error('Error fetching docs index:', error);
    return NextResponse.json(
      { error: 'Failed to fetch index.md' },
      { status: 500 },
    );
  }
}
