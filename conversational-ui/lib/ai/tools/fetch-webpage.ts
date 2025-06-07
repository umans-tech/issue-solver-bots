import { DataStreamWriter, tool } from 'ai';
import { z } from 'zod';
import { Session } from 'next-auth';
import { chromium } from 'playwright';
import { Readability } from '@mozilla/readability';
import { JSDOM } from 'jsdom';

export interface FetchWebpageProps {
  session: Session;
  dataStream: DataStreamWriter;
}

export const fetchWebpage = ({ dataStream }: FetchWebpageProps) => tool({
  description: 'Fetch and extract readable content from a webpage URL. Handles both static and dynamic websites.',
  parameters: z.object({
    url: z.string().url().describe('The URL to fetch content from'),
  }),
  execute: async ({ url }) => {
    try {
      console.log(`Fetching webpage: ${url}`);
      
      // Launch browser
      const browser = await chromium.launch();
      const page = await browser.newPage();
      
      // Set a reasonable timeout and user agent
      await page.setExtraHTTPHeaders({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
      });
      
      // Navigate to the page with timeout
      await page.goto(url, { 
        waitUntil: 'domcontentloaded',
        timeout: 30000 
      });
      
      // Wait a bit for dynamic content to load
      await page.waitForTimeout(2000);
      
      // Get the HTML content
      const htmlContent = await page.content();
      
      // Close browser
      await browser.close();
      
      // Parse with JSDOM for Readability
      const dom = new JSDOM(htmlContent, { url });
      const document = dom.window.document;
      
      // Extract readable content with Readability
      const reader = new Readability(document);
      const article = reader.parse();
      
      if (!article) {
        return `Failed to extract readable content from ${url}. The page might not contain article-like content.`;
      }
      
      // Write source information to dataStream
      dataStream.writeSource({
        sourceType: 'url',
        id: crypto.randomUUID(),
        url: url,
        title: article.title || 'Webpage Content',
      });
      
      // Return the extracted content
      const result = {
        url,
        title: article.title || 'No title found',
        content: article.textContent || '',
        excerpt: article.excerpt || '',
        wordCount: article.textContent?.split(/\s+/).length || 0,
      };
      
      console.log(`Successfully fetched webpage: ${url}, ${result.wordCount} words`);
      
      return `# ${result.title}

    **URL:** ${result.url}\n\n
    **Word Count:** ${result.wordCount}\n\n

    ${result.excerpt ? `**Excerpt:** ${result.excerpt}\n\n` : ''}

    ## Content

    ${result.content}`;
        
        } catch (error) {
        console.error('Error fetching webpage:', error);
        
        if (error instanceof Error) {
            if (error.message.includes('timeout')) {
            return `Failed to fetch ${url}: The page took too long to load (timeout after 30 seconds).`;
            }
            if (error.message.includes('net::ERR_NAME_NOT_RESOLVED')) {
            return `Failed to fetch ${url}: Domain name could not be resolved.`;
            }
            if (error.message.includes('net::ERR_CONNECTION_REFUSED')) {
            return `Failed to fetch ${url}: Connection was refused by the server.`;
            }
        }
        
        return `Failed to fetch content from ${url}: ${error instanceof Error ? error.message : String(error)}`;
        }
    },
}); 