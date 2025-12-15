import { z } from 'zod';
import { tool, type UIMessageStreamWriter } from 'ai';
import type { Session } from 'next-auth';
import { OpenAI } from 'openai';
import type { ChatMessage } from '@/lib/types';

const client = new OpenAI();

// Interface for codebaseSearch props
interface CodebaseSearchProps {
  session: Session;
  dataStream: UIMessageStreamWriter<ChatMessage>;
}

function formatResults(results: any) {
  let formattedResults = '';
  for (const result of results.data) {
    let formattedResult = `<result file_name='${result.attributes.file_name}' file_path='${result.attributes.file_path}'>`;
    for (const part of result.content) {
      formattedResult += `<content>${part.text}</content>`;
    }
    formattedResults += `${formattedResult}</result>`;
  }
  return `<sources>${formattedResults}</sources>`;
}

// Helper function to log search operations
function logSearchOperation(operation: string, data: any) {
  const timestamp = new Date().toISOString();
  console.log(
    `[${timestamp}] CodebaseSearch ${operation}:`,
    JSON.stringify(data, null, 2),
  );
}

// Helper function to parse filters parameter that may come as string or object
function parseFilters(filters: any) {
  if (!filters) return undefined;

  // If filters is already an object, return as-is
  if (typeof filters === 'object' && filters !== null) {
    return filters;
  }

  // If filters is a string, try to parse it as JSON
  if (typeof filters === 'string') {
    try {
      return JSON.parse(filters);
    } catch (error) {
      console.warn('Failed to parse filters JSON string:', error);
      return undefined;
    }
  }

  return undefined;
}

export const codebaseSearch = ({ session, dataStream }: CodebaseSearchProps) =>
  tool({
    description: `Search the codebase using hybrid semantic search to find relevant code snippets. ${session.user?.selectedSpace?.connectedRepoUrl ? `The user connected this repository: ${session.user?.selectedSpace?.connectedRepoUrl}. Keep this in mind if the user refer to a codebase.` : 'The user has not connected any code repo yet.'}`,
    inputSchema: z.object({
      query: z
        .string()
        .describe(
          'The search query to find relevant code and files snippets in the codebase.',
        ),
      filter_type: z
        .enum(['eq', 'ne', 'and', 'or', 'none'])
        .describe(
          'Filter type: eq (equals), ne (not equals), and, or, or none for no filtering. Use "none" if no filter is needed.',
        ),
      filter_key: z
        .enum(['file_name', 'file_path', 'file_extension', 'none'])
        .describe(
          'The attribute to filter on. Use "none" if filter_type is "none" or for compound filters.',
        ),
      filter_value: z
        .string()
        .describe(
          'The value to match (e.g., ".ts" for file_extension, "index.ts" for file_name). Use empty string "" if filter_type is "none" or for compound filters.',
        ),
      compound_filters: z
        .string()
        .describe(
          'For AND/OR filters only: JSON array of filters, e.g., [{"type":"eq","key":"file_extension","value":".ts"},{"type":"eq","key":"file_name","value":"index.ts"}]. Use empty string "" for simple filters or no filter.',
        ),
    }),
    execute: async ({
      query,
      filter_type,
      filter_key,
      filter_value,
      compound_filters,
    }) => {
      // Build filters from the separate parameters
      let filters = undefined;
      if (
        filter_type !== 'none' &&
        filter_type !== 'and' &&
        filter_type !== 'or'
      ) {
        // Simple filter
        if (filter_key !== 'none' && filter_value) {
          filters = {
            type: filter_type,
            key: filter_key,
            value: filter_value,
          };
        }
      } else if (
        (filter_type === 'and' || filter_type === 'or') &&
        compound_filters
      ) {
        // Compound filter
        try {
          const parsedCompoundFilters = JSON.parse(compound_filters);
          filters = {
            type: filter_type,
            filters: parsedCompoundFilters,
          };
        } catch (e) {
          console.warn('Failed to parse compound_filters:', e);
        }
      }

      // Parse filters to handle both string and object formats
      const parsedFilters = parseFilters(filters);

      try {
        // Log the search request
        logSearchOperation('REQUEST', { query, filters: parsedFilters });

        // Get the knowledge base ID from the session object, checking session locations
        const knowledgeBaseId =
          // @ts-expect-error - Accessing properties that TypeScript doesn't know about
          session.knowledgeBaseId ||
          session?.user?.selectedSpace?.knowledgeBaseId;

        if (!knowledgeBaseId) {
          logSearchOperation('ERROR', 'No knowledge base found');
          return 'No knowledge base found for this user. Please connect a repository first.';
        }

        logSearchOperation('KNOWLEDGE_BASE', { knowledgeBaseId });

        console.time('codebaseSearch:execution');
        const searchResults = await client.vectorStores.search(
          knowledgeBaseId,
          {
            query: query,
            rewrite_query: true,
            filters: parsedFilters,
          },
        );
        console.timeEnd('codebaseSearch:execution');

        // Log search results summary (not the full results to avoid logging sensitive information)
        logSearchOperation('RESULTS_SUMMARY', {
          resultCount: searchResults.data?.length || 0,
          knowledgeBaseId,
          query,
        });

        // Format the results in XML
        const formattedResult = formatResults(searchResults);
        for (const result of searchResults.data) {
          dataStream.write({
            type: 'source-url',
            sourceId: result.file_id,
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
          filters: parsedFilters,
        });
        console.error('Error searching codebase:', error);
        return `Error searching codebase: ${error instanceof Error ? error.message : String(error)}`;
      }
    },
  });
