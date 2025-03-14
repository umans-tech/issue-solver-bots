import { z } from 'zod';
import { tool } from 'ai';
import { Session } from 'next-auth';
import { DataStreamWriter } from 'ai';
import { OpenAI } from 'openai';
import { getKnowledgeBaseId } from '@/lib/utils';

const client = new OpenAI();

// Interface for codebaseSearch props
interface CodebaseSearchProps {
  session: Session;
  dataStream: DataStreamWriter;
}


function formatResults(results: any) {
    let formattedResults = '';
    for (const result of results.data) {
        let formattedResult = `<result file_id='${result.file_id}' file_name='${result.file_name}'>`;
        for (const part of result.content) {
            formattedResult += `<content>${part.text}</content>`;
        }
        formattedResults += formattedResult + "</result>";
    }
    return `<sources>${formattedResults}</sources>`;
}

export const codebaseSearch = ({ session }: CodebaseSearchProps) => tool({
  description: 'Search the codebase using hybrid semantic search to find relevant code snippets.',
  parameters: z.object({
    query: z.string().describe('The search query to find relevant code and files snippets in the codebase.'),
  }),
  execute: async ({ query }) => {
    try {
      // Get the knowledge base ID from the session object
      // @ts-ignore - Accessing a property that TypeScript doesn't know about
      const knowledgeBaseId = session.knowledgeBaseId || getKnowledgeBaseId();
      
      if (!knowledgeBaseId) {
        return 'No knowledge base found for this user. Please connect a repository first.';
      }
      
      const searchResults = await client.vectorStores.search(knowledgeBaseId, {
        query: query,
      });
      
      // Format the results in XML
      return formatResults(searchResults);
    } catch (error) {
      console.error('Error searching codebase:', error);
      return `Error searching codebase: ${error instanceof Error ? error.message : String(error)}`;
    }
  },
});