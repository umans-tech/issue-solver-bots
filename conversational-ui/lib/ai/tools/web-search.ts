import { tool, type UIMessageStreamWriter } from 'ai';
import { z } from 'zod';
import Exa from 'exa-js';
import type { Session } from 'next-auth';
import type { ChatMessage } from '@/lib/types';

export const exa = new Exa(process.env.EXA_API_KEY);

export interface WebSearchProps {
  session: Session;
  dataStream: UIMessageStreamWriter<ChatMessage>;
}

export const webSearch = ({ session, dataStream }: WebSearchProps) =>
  tool({
    description: 'Search the web for up-to-date information',
    inputSchema: z.object({
      query: z.string().min(1).max(100).describe('The search query'),
    }),
    execute: async ({ query }) => {
      const { results } = await exa.searchAndContents(query, {
        livecrawl: 'preferred',
        numResults: 5,
      });
      for (const result of results) {
        dataStream.write({
          type: 'source-url',
          sourceId: crypto.randomUUID(),
          url: result.url,
          title: result.title || '',
          providerMetadata: {
            exa: {
              publishedDate: result.publishedDate || null,
            },
          },
        });
      }
      return results.map((result) => ({
        title: result.title,
        url: result.url,
        content: result.text,
        publishedDate: result.publishedDate,
      }));
    },
  });
