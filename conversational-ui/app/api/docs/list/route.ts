import { NextResponse } from 'next/server';
import { S3Client, ListObjectsV2Command } from '@aws-sdk/client-s3';
import { auth } from '@/app/(auth)/auth';

export async function GET(request: Request) {
  try {
    const session = await auth();
    if (!session?.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { searchParams } = new URL(request.url);
    const kbId = searchParams.get('kbId') || session.user.selectedSpace?.knowledgeBaseId;
    const commitSha = searchParams.get('commitSha');
    if (!kbId || !commitSha) return NextResponse.json({ error: 'kbId and commitSha are required' }, { status: 400 });

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

    const prefix = `base/${kbId}/docs/${commitSha}/`;
    let continuationToken: string | undefined = undefined;
    const files: string[] = [];
    do {
      const listCmd: ListObjectsV2Command = new ListObjectsV2Command({ Bucket: BUCKET_NAME, Prefix: prefix, ContinuationToken: continuationToken });
      const res = await s3Client.send(listCmd);
      (res.Contents || []).forEach(obj => {
        const key = obj.Key || '';
        if (key.endsWith('.md')) {
          files.push(key.substring(prefix.length));
        }
      });
      continuationToken = res.IsTruncated ? res.NextContinuationToken : undefined;
    } while (continuationToken);

    // Sort alphabetically, keep index.md first if present
    files.sort((a, b) => a.localeCompare(b));
    const indexFirst = files.includes('index.md') ? ['index.md', ...files.filter(f => f !== 'index.md')] : files;

    return NextResponse.json({ files: indexFirst });
  } catch (error) {
    console.error('List docs error', error);
    return NextResponse.json({ error: 'Failed to list docs' }, { status: 500 });
  }
}


