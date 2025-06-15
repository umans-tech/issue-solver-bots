import { tool } from 'ai';
import { z } from 'zod';
import { Session } from 'next-auth';
import { DataStreamWriter } from 'ai';

export interface ConnectRepositoryProps {
  session: Session;
  dataStream: DataStreamWriter;
}

export const connectRepository = ({ session, dataStream }: ConnectRepositoryProps) => tool({
  description: 'Show repository connection interface to allow users to connect their code repository',
  parameters: z.object({
    message: z.string().optional().describe('Optional message to display with the repository connection form'),
  }),
  // No execute function - this will trigger the human-in-the-loop flow
});

// Separate execute function for when user submits the form
export async function executeConnectRepository(params: {
  repoUrl: string;
  accessToken?: string;
  userId: string;
  spaceId: string;
  knowledgeBaseId?: string;
  processId?: string;
  status?: string;
}) {
  console.log('🔧 executeConnectRepository executing with params:', params);
  
  // The frontend has already made the connection and passed the results
  // We just need to format the response for the AI to understand
  
  if (params.knowledgeBaseId) {
    // Repository was successfully connected by the frontend
    return {
      action: 'repository_connected',
      status: 'success',
      knowledgeBaseId: params.knowledgeBaseId,
      processId: params.processId,
      repoUrl: params.repoUrl,
      message: 'Repository connected successfully!',
    };
  } else {
    // Connection failed or was cancelled
    return {
      action: 'repository_connection_failed',
      status: 'error',
      error: 'Repository connection was not completed',
    };
  }
} 