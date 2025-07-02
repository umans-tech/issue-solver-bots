import { z } from 'zod';
import { tool } from 'ai';
import { Session } from 'next-auth';
import { DataStreamWriter } from 'ai';
import { OpenAI } from 'openai';

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

// Helper function to log search operations
function logSearchOperation(operation: string, data: any) {
  const timestamp = new Date().toISOString();
  console.log(`[${timestamp}] CodebaseSearch ${operation}:`, JSON.stringify(data, null, 2));
}

export const codebaseSearch = ({ session, dataStream }: CodebaseSearchProps) => tool({
  description: `Search the codebase using hybrid semantic search to find relevant code snippets. ${session.user?.selectedSpace?.connectedRepoUrl ? `The user connected this repository: ${session.user?.selectedSpace?.connectedRepoUrl}. Keep this in mind if the user refer to a codebase.` : 'The user has not connected any code repo yet.'}`,
  parameters: z.object({
    query: z.string().describe('The search query to find relevant code and files snippets in the codebase.'),
    filters: z.union([filterSchema, z.string()]).optional().describe('Optional filters to narrow down search results based on file attributes. Can be provided as an object or JSON string. Available attributes to filter on are: "file_name" (string), "file_path" (string) and "file_extension" (string). Example: { "type": "eq", "key": "file_name", "value": "index.js" } or as JSON string: "{\\"type\\":\\"eq\\",\\"key\\":\\"file_name\\",\\"value\\":\\"index.js\\"}" or a compound filter like { "type": "and", "filters": [{ "type": "eq", "key": "file_name", "value": "index.js" }, { "type": "eq", "key": "file_path", "value": "/src/components/" }, { "type": "eq", "key": "file_extension", "value": ".js" }] }'),
  }),
  execute: async ({ query, filters }) => {
    // Preprocess filters: handle both string and object formats
    let processedFilters = filters;
    if (typeof filters === 'string' && filters.trim()) {
      try {
        processedFilters = JSON.parse(filters);
        logSearchOperation('FILTER_PARSING', { originalFilters: filters, parsedFilters: processedFilters });
      } catch (parseError) {
        logSearchOperation('FILTER_PARSE_ERROR', { 
          originalFilters: filters, 
          parseError: parseError instanceof Error ? parseError.message : String(parseError) 
        });
        return `Error parsing filters: Invalid JSON format. Please provide filters as a valid JSON object.`;
      }
    }

    try {

      // Log the search request with processed filters
      logSearchOperation('REQUEST', { query, filters: processedFilters });

      // Get the knowledge base ID from the session object, checking session locations
      // @ts-ignore - Accessing properties that TypeScript doesn't know about
      const knowledgeBaseId = session.knowledgeBaseId ||
                             session?.user?.selectedSpace?.knowledgeBaseId;

      if (!knowledgeBaseId) {
        logSearchOperation('ERROR', 'No knowledge base found');
        return 'No knowledge base found for this user. Please connect a repository first.';
      }

      logSearchOperation('KNOWLEDGE_BASE', { knowledgeBaseId });

      console.time('codebaseSearch:execution');
      const searchResults = await client.vectorStores.search(knowledgeBaseId, {
        query: query,
        rewrite_query: true,
        filters: processedFilters,
      });
      console.timeEnd('codebaseSearch:execution');

      // Log search results summary (not the full results to avoid logging sensitive information)
      logSearchOperation('RESULTS_SUMMARY', {
        resultCount: searchResults.data?.length || 0,
        knowledgeBaseId,
        query
      });

      // Format the results in XML
      const formattedResult = formatResults(searchResults);
      for (const result of searchResults.data) {
        dataStream.writeSource({
          sourceType: 'url',
          id: result.file_id,
          url: result.attributes?.file_path as string,
          title: result.attributes?.file_name as string,
        });
      }
      return formattedResult;
    } catch (error) {
      // Log error
      logSearchOperation('ERROR', {
        error: error instanceof Error ? error.message : String(error),
        query,
        filters: processedFilters
      });
      console.error('Error searching codebase:', error);
      return `Error searching codebase: ${error instanceof Error ? error.message : String(error)}`;
    }
  },
});
