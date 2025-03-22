import { z } from 'zod';
import { tool } from 'ai';
import { Session } from 'next-auth';
import { DataStreamWriter } from 'ai';
import { OpenAI } from 'openai';
import { getKnowledgeBaseId } from '@/lib/utils';

const client = new OpenAI();

// Define Zod schemas for filters
const comparisonFilterSchema = z.object({
  type: z.enum(['eq', 'ne', 'gt', 'gte', 'lt', 'lte']),
  key: z.string(),
  value: z.union([z.string(), z.number(), z.boolean()])
});

// Define compound filter without recursion
const compoundFilterSchema = z.object({
  type: z.enum(['and', 'or']),
  filters: z.array(
    z.union([
      comparisonFilterSchema,
      z.object({
        type: z.enum(['and', 'or']),
        filters: z.array(comparisonFilterSchema)
      })
    ])
  )
});

// Combined filter schema for accepting either type
const filterSchema = z.union([comparisonFilterSchema, compoundFilterSchema]).optional();

// Interface for codebaseSearch props
interface CodebaseSearchProps {
  session: Session;
  dataStream: DataStreamWriter;
}


function formatResults(results: any) {
    let formattedResults = '';
    for (const result of results.data) {
        let formattedResult = `<result file_name='${result.attributes.file_name}' file_path='${result.attributes.file_path}'>`;
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
    filters: filterSchema.describe('Optional filters to narrow down search results based on file attributes.'),
  }),
  execute: async ({ query, filters }) => {
    try {
      // Get the knowledge base ID from the session object
      // @ts-ignore - Accessing a property that TypeScript doesn't know about
      const knowledgeBaseId = session.knowledgeBaseId || getKnowledgeBaseId();
      
      if (!knowledgeBaseId) {
        return 'No knowledge base found for this user. Please connect a repository first.';
      }
      
      const searchResults = await client.vectorStores.search(knowledgeBaseId, {
        query: query,
        rewrite_query: true,
        filters: filters,
      });
      
      // Format the results in XML
      return formatResults(searchResults);
    } catch (error) {
      console.error('Error searching codebase:', error);
      return `Error searching codebase: ${error instanceof Error ? error.message : String(error)}`;
    }
  },
});