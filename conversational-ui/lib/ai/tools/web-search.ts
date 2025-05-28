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
    const { results } = await exa.searchAndContents(query, {
      livecrawl: 'always',
      numResults: 5,
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
    return results.map(result => ({
      title: result.title,
      url: result.url,
      content: result.text,
      publishedDate: result.publishedDate,
    }));
  },
});