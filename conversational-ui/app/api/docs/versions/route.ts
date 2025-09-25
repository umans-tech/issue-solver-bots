import { NextResponse } from 'next/server';
import { S3Client, ListObjectsV2Command } from '@aws-sdk/client-s3';
import { auth } from '@/app/(auth)/auth';
import { getCachedProcess, setCachedProcess } from '@/lib/process-cache';
import { extractRepositoryIndexedEvents } from '@/lib/repository-events';

export async function GET(request: Request) {
  try {
    const session = await auth();
    if (!session?.user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const { searchParams } = new URL(request.url);
    const kbId = searchParams.get('kbId') || session.user.selectedSpace?.knowledgeBaseId;
    if (!kbId) return NextResponse.json({ error: 'kbId is required' }, { status: 400 });

    let versions: string[] = [];

    const selectedSpace = session.user.selectedSpace;
    const processId = selectedSpace?.processId;
    const isMatchingSpace = selectedSpace?.knowledgeBaseId && selectedSpace.knowledgeBaseId === kbId;

    if (processId && isMatchingSpace) {
      let processData = getCachedProcess(processId);
      if (!processData) {
        const cuduEndpoint = process.env.CUDU_ENDPOINT;
        if (!cuduEndpoint) {
          console.error('CUDU API endpoint is not configured');
        } else {
          const apiUrl = `${cuduEndpoint}/processes/${processId}`;
          try {
            const response = await fetch(apiUrl, {
              method: 'GET',
              headers: {
                'Content-Type': 'application/json',
              },
            });
            if (response.ok) {
              processData = await response.json();
              setCachedProcess(processId, processData);
            } else {
              console.warn(`Failed to fetch process snapshot for versions (${response.status})`);
            }
          } catch (error) {
            console.error('Error fetching process snapshot for versions:', error);
          }
        }
      }

      if (processData) {
        const indexed = extractRepositoryIndexedEvents(processData.events);
        versions = indexed.map((entry) => entry.sha);
      }
    }

    if (versions.length === 0) {
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
      if (res.CommonPrefixes) {
        for (const cp of res.CommonPrefixes) {
          const p = cp.Prefix || '';
          const parts = p.split('/');
          const sha = parts.filter(Boolean).pop();
          if (sha) versions.push(sha);
        }
      }
    }

    return NextResponse.json({ versions });
  } catch (error) {
    console.error('Error listing versions:', error);
    return NextResponse.json({ error: 'Failed to list versions' }, { status: 500 });
  }
}

