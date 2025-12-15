import { NextResponse } from 'next/server';
import {
  GetObjectCommand,
  PutObjectCommand,
  S3Client,
} from '@aws-sdk/client-s3';

import { auth } from '@/app/(auth)/auth';

type Manifest = Record<string, Record<string, string>>;

async function streamToString(stream: any): Promise<string> {
  return new Promise((resolve, reject) => {
    const chunks: any[] = [];
    stream.on('data', (chunk: any) => chunks.push(Buffer.from(chunk)));
    stream.on('error', (err: any) => reject(err));
    stream.on('end', () => resolve(Buffer.concat(chunks).toString('utf-8')));
  });
}

async function loadManifest(
  s3Client: S3Client,
  bucket: string,
  key: string,
): Promise<Manifest> {
  try {
    const res = await s3Client.send(
      new GetObjectCommand({ Bucket: bucket, Key: key }),
    );
    const bodyString = await streamToString(res.Body);
    const parsed = JSON.parse(bodyString);
    return parsed && typeof parsed === 'object' ? parsed : {};
  } catch (error) {
    return {};
  }
}

export async function POST(request: Request) {
  const session = await auth();
  if (!session?.user)
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

  const body = await request.json().catch(() => null);
  const kbId = body?.kbId || session.user.selectedSpace?.knowledgeBaseId;
  const commitSha = body?.commitSha;
  const path = body?.path;
  const action = body?.action;

  if (
    !kbId ||
    !commitSha ||
    !path ||
    (action !== 'approve' && action !== 'revoke')
  ) {
    return NextResponse.json(
      { error: 'kbId, commitSha, path and action are required' },
      { status: 400 },
    );
  }

  const bucket = process.env.BLOB_BUCKET_NAME || '';
  const s3Client = new S3Client({
    region: process.env.BLOB_REGION || '',
    endpoint: process.env.BLOB_ENDPOINT || '',
    forcePathStyle: !!process.env.BLOB_ENDPOINT,
    credentials: {
      accessKeyId: process.env.BLOB_ACCESS_KEY_ID || '',
      secretAccessKey: process.env.BLOB_READ_WRITE_TOKEN || '',
    },
  });

  const manifestKey = `base/${kbId}/docs/${commitSha}/__metadata__.json`;

  const manifest = await loadManifest(s3Client, bucket, manifestKey);
  const existingEntry = manifest[path] || {};

  if (action === 'approve') {
    manifest[path] = {
      ...existingEntry,
      approved_by_id: session.user.id,
      approved_by_name: session.user.name || session.user.email || 'Unknown',
      approved_at: new Date().toISOString(),
    };
  } else {
    const { approved_by_id, approved_by_name, approved_at, ...rest } =
      existingEntry;
    manifest[path] = rest;
  }

  await s3Client.send(
    new PutObjectCommand({
      Bucket: bucket,
      Key: manifestKey,
      Body: JSON.stringify(manifest),
      ContentType: 'application/json',
    }),
  );

  return NextResponse.json({ metadata: manifest[path] });
}
