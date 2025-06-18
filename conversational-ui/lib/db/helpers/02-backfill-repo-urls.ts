import { config } from 'dotenv';
import postgres from 'postgres';
import { drizzle } from 'drizzle-orm/postgres-js';
import { and, isNotNull, isNull, eq } from 'drizzle-orm';
import { space } from '../schema';

config({
  path: '.env.local',
});

if (!process.env.POSTGRES_URL) {
  throw new Error('POSTGRES_URL environment variable is not set');
}

if (!process.env.CUDU_ENDPOINT) {
  throw new Error('CUDU_ENDPOINT environment variable is not set');
}

const client = postgres(process.env.POSTGRES_URL);
const db = drizzle(client);

async function getRepoUrlFromBackend(knowledgeBaseId: string): Promise<string | null> {
  try {
    const response = await fetch(`${process.env.CUDU_ENDPOINT}/processes?knowledge_base_id=${knowledgeBaseId}`);
    
    if (!response.ok) {
      console.warn(`Failed to fetch repo info for knowledge base ${knowledgeBaseId}: ${response.statusText}`);
      return null;
    }
    
    const data = await response.json();
    
    // Look for repo URL in the response
    const repoUrl = data.repo_url || data.repository_url || data.git_url || data.url;
    
    if (repoUrl && typeof repoUrl === 'string') {
      return repoUrl;
    }
    
    // If processes array exists, look in the first process
    if (data.processes && Array.isArray(data.processes) && data.processes.length > 0) {
      const process = data.processes[0];
      
      // Check direct process fields
      const processRepoUrl = process.repo_url || process.repository_url || process.git_url || process.url || null;
      if (processRepoUrl) {
        return processRepoUrl;
      }
      
      // Check in events array for repository_connected event
      if (process.events && Array.isArray(process.events)) {
        const repoConnectedEvent = process.events.find((event: any) => event.type === 'repository_connected');
        if (repoConnectedEvent && repoConnectedEvent.url) {
          return repoConnectedEvent.url;
        }
      }
    }
    
    return null;
  } catch (error) {
    console.error(`Error fetching repo info for knowledge base ${knowledgeBaseId}:`, error);
    return null;
  }
}

async function backfillConnectedRepoUrls() {
  console.info('Starting backfill of connectedRepoUrl for existing spaces...');
  
  // Find all spaces with connected repos but missing repo URLs
  const spacesNeedingBackfill = await db
    .select({
      id: space.id,
      name: space.name,
      knowledgeBaseId: space.knowledgeBaseId,
    })
    .from(space)
    .where(
      and(
        isNotNull(space.knowledgeBaseId),
        isNull(space.connectedRepoUrl)
      )
    );

  console.info(`Found ${spacesNeedingBackfill.length} spaces needing repo URL backfill`);

  if (spacesNeedingBackfill.length === 0) {
    console.info('No spaces need backfilling. All done!');
    return;
  }

  let spacesProcessed = 0;
  let spacesUpdated = 0;
  let spacesSkipped = 0;
  const errors: Array<{ spaceId: string; error: string }> = [];

  // Process each space
  for (const spaceRecord of spacesNeedingBackfill) {
    spacesProcessed++;
    
    try {
      console.info(`Processing space "${spaceRecord.name}" (${spaceRecord.id})`);
      
      // Get repo URL from backend
      const repoUrl = await getRepoUrlFromBackend(spaceRecord.knowledgeBaseId!);
      
      if (!repoUrl) {
        console.warn(`No repo URL found for space "${spaceRecord.name}" with knowledge base ${spaceRecord.knowledgeBaseId}`);
        spacesSkipped++;
        continue;
      }
      
      // Update the space - this is idempotent because of the WHERE clause
      const updateResult = await db
        .update(space)
        .set({
          connectedRepoUrl: repoUrl,
          updatedAt: new Date(),
        })
        .where(
          and(
            isNotNull(space.knowledgeBaseId),
            isNull(space.connectedRepoUrl),
            eq(space.id, spaceRecord.id)
          )
        )
        .returning({ id: space.id });

      if (updateResult.length > 0) {
        console.info(`Updated space "${spaceRecord.name}" with repo URL: ${repoUrl}`);
        spacesUpdated++;
      } else {
        console.info(`Space "${spaceRecord.name}" was already updated`);
        spacesSkipped++;
      }
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Error processing space "${spaceRecord.name}":`, errorMessage);
      errors.push({
        spaceId: spaceRecord.id,
        error: errorMessage,
      });
    }
  }

  console.info(`Backfill completed: ${spacesProcessed} spaces processed, ${spacesUpdated} updated, ${spacesSkipped} skipped, ${errors.length} errors`);
  
  if (errors.length > 0) {
    console.error('Errors encountered:');
    errors.forEach(error => {
      console.error(`Space ${error.spaceId}: ${error.error}`);
    });
  }
}

backfillConnectedRepoUrls()
  .then(() => {
    console.info('Script completed successfully');
    process.exit(0);
  })
  .catch((error) => {
    console.error('Script failed:', error);
    process.exit(1);
  }); 