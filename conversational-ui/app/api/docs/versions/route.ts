import { NextResponse } from 'next/server';
import { S3Client, ListObjectsV2Command } from '@aws-sdk/client-s3';
import { auth } from '@/app/(auth)/auth';

export async function GET(request: Request) {
  try {
    const session = await auth();
    if (!session?.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { searchParams } = new URL(request.url);
    const kbId = searchParams.get('kbId') || session.user.selectedSpace?.knowledgeBaseId;
    if (!kbId) return NextResponse.json({ error: 'kbId is required' }, { status: 400 });

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

    const prefix = `base/${kbId}/docs/`;
    const cmd = new ListObjectsV2Command({ Bucket: BUCKET_NAME, Prefix: prefix, Delimiter: '/' });
    const res = await s3Client.send(cmd);
    const versions: string[] = [];
    if (res.CommonPrefixes) {
      for (const cp of res.CommonPrefixes) {
        const p = cp.Prefix || '';
        const parts = p.split('/');
        const sha = parts.filter(Boolean).pop();
        if (sha) versions.push(sha);
      }
    }
    return NextResponse.json({ versions });
  } catch (error) {
    console.error('Error listing versions:', error);
    return NextResponse.json({ error: 'Failed to list versions' }, { status: 500 });
  }
}


