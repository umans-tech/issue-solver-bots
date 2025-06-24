import { DataStreamWriter, tool } from 'ai';
import { z } from 'zod';
import Exa from 'exa-js';
import { Session } from 'next-auth';

export const exa = new Exa(process.env.EXA_API_KEY);

export interface WebSearchProps {
  session: Session;
  dataStream: DataStreamWriter;
}

export const webSearch = ({ session, dataStream }: WebSearchProps) => tool({
  description: 'Search the web for up-to-date information',
  parameters: z.object({
    query: z.string().min(1).max(100).describe('The search query'),
  }),
  execute: async ({ query }) => {
    try {
      const { results } = await exa.searchAndContents(query, {
        livecrawl: 'preferred', // cspell:disable-line
        numResults: 10,
      });
      
      for (const result of results) {
        dataStream.writeSource({
          sourceType: 'url',
          id: crypto.randomUUID(),
          url: result.url,
          title: result.title || '',
          providerMetadata: {
            exa: {
              publishedDate: result.publishedDate || null
            }
          },
        });
      }
      
      const mappedResults = results.map(result => ({
        title: result.title,
        url: result.url,
        content: result.text
          ?.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, ' ') // Remove problematic control chars but keep \t(0x09), \n(0x0A), \r(0x0D)
          ?.trim(),
        publishedDate: result.publishedDate,
      }));
      
      return mappedResults;
    } catch (error) {
      console.error('[WebSearch] Error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      return `Web search failed: ${errorMessage}. Please try a different query or check your internet connection.`;
    }
  },
});