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
  execute: async ({ message }) => {
    console.log('🔧 connectRepository tool executing...');
    
    // Return immediately with UI data
    return {
      action: 'show_repository_connection',
      message: message || 'Please connect your repository to get started:',
      status: 'pending_user_action',
    };
  },
}); 