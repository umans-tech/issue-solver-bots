import { NextResponse } from 'next/server';
import { ListObjectsV2Command, S3Client } from '@aws-sdk/client-s3';
import { auth } from '@/app/(auth)/auth';

export async function GET(request: Request) {
  try {
    const session = await auth();
    if (!session?.user)
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { searchParams } = new URL(request.url);
    const kbId =
      searchParams.get('kbId') || session.user.selectedSpace?.knowledgeBaseId;
    if (!kbId)
      return NextResponse.json({ error: 'kbId is required' }, { status: 400 });

    const versions = await listVersionsFromBlobStorage(kbId);
    return NextResponse.json({ versions });
  } catch (error) {
    console.error('Error listing versions:', error);
    return NextResponse.json(
      { error: 'Failed to list versions' },
      { status: 500 },
    );
  }
}

async function listVersionsFromBlobStorage(kbId: string): Promise<string[]> {
  const bucketName = process.env.BLOB_BUCKET_NAME || '';
  if (!bucketName) {
    console.error('BLOB_BUCKET_NAME is not configured');
    return [];
  }

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
  const seen = new Map<string, number>();
  let continuationToken: string | undefined;

  do {
    const cmd = new ListObjectsV2Command({
      Bucket: bucketName,
      Prefix: prefix,
      ContinuationToken: continuationToken,
    });
    const res = await s3Client.send(cmd);

    for (const obj of res.Contents ?? []) {
      const key = obj.Key;
      if (!key || !key.startsWith(prefix)) continue;

      const remainder = key.slice(prefix.length);
      if (!remainder) continue;

      const sha = remainder.split('/')[0]?.trim();
      if (!sha) continue;

      const lastModified = obj.LastModified ? obj.LastModified.getTime() : 0;
      const previous = seen.get(sha) ?? 0;
      if (lastModified >= previous) {
        seen.set(sha, lastModified);
      }
    }

    continuationToken = res.IsTruncated ? res.NextContinuationToken : undefined;
  } while (continuationToken);

  return Array.from(seen.entries())
    .sort((a, b) => a[1] - b[1])
    .map(([sha]) => sha);
}
