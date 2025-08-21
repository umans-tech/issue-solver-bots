import { type UIMessageStreamWriter, tool } from 'ai';
import { z } from 'zod';
import { Session } from 'next-auth';
import { chromium, Browser, Page } from 'playwright';
import { Readability } from '@mozilla/readability';
import { JSDOM } from 'jsdom';
import { readdirSync } from 'fs';
import { join } from 'path';
import { ChatMessage } from '@/lib/types';

export interface FetchWebpageProps {
  session: Session;
  dataStream: UIMessageStreamWriter<ChatMessage>;
}

export const fetchWebpage = ({ dataStream }: FetchWebpageProps) => tool({
  description: 'Fetch and extract readable content from a webpage URL. Handles both static and dynamic websites.',
  inputSchema: z.object({
    url: z.string().describe('The URL to fetch content from. Must be a valid HTTP or HTTPS URL.'),
  }),
  execute: async ({ url }) => {
    let browser: Browser | null = null;
    let page: Page | null = null;
    
    try {
      const startTime = Date.now();
      console.log(`Fetching webpage: ${url}`);
      
      // Helper function to find Chromium executable in production
      const getChromiumExecutablePath = () => {
        if (process.env.NODE_ENV !== 'production' || !process.env.PLAYWRIGHT_BROWSERS_PATH) {
          return undefined;
        }
        
        try {
          const browsersPath = process.env.PLAYWRIGHT_BROWSERS_PATH;
          const chromiumDirs = readdirSync(browsersPath).filter(dir => dir.startsWith('chromium-'));
          
          if (chromiumDirs.length === 0) {
            console.warn('No Chromium installation found in browsers path');
            return undefined;
          }
          
          const chromiumPath = join(browsersPath, chromiumDirs[0], 'chrome-linux', 'chrome');
          console.log(`Using Chromium executable: ${chromiumPath}`);
          return chromiumPath;
        } catch (error) {
          console.error('Error finding Chromium executable:', error);
          return undefined;
        }
      };

      // Launch browser with production-ready configuration
      const launchOptions = {
        headless: true,
        timeout: 30000,
        ...(process.env.NODE_ENV === 'production' && {
          executablePath: getChromiumExecutablePath(),
          args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
            '--no-first-run',
            '--no-zygote',
            '--single-process',
            '--disable-extensions',
            '--disable-default-apps',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding'
          ]
        })
      };
      
      browser = await chromium.launch(launchOptions);
      page = await browser.newPage();
      
      // Set up error monitoring
      page.on('console', msg => {
        if (msg.type() === 'error') {
          console.error('Browser console error:', msg.text());
        }
      });
      
      page.on('pageerror', error => {
        console.error('Page error:', error.message);
      });
      
      // Set a reasonable timeout and user agent
      await page.setExtraHTTPHeaders({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
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
      dataStream.write({
        type: 'source-url',
        sourceId: crypto.randomUUID(),
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
      
      const endTime = Date.now();
      const duration = endTime - startTime;
      console.log(`Successfully fetched webpage: ${url}, ${result.wordCount} words, took ${duration}ms`);
      
      // Log memory usage for monitoring
      const memUsage = process.memoryUsage();
      console.log(`Memory usage - RSS: ${Math.round(memUsage.rss / 1024 / 1024)}MB, Heap: ${Math.round(memUsage.heapUsed / 1024 / 1024)}MB`);
      
      return `# ${result.title}

    **URL:** ${result.url}\n\n
    **Word Count:** ${result.wordCount}\n\n

    ${result.excerpt ? `**Excerpt:** ${result.excerpt}\n\n` : ''}

    ## Content

    ${result.content}`;
        
        } catch (error) {
        console.error('Error fetching webpage:', error);
        
        if (error instanceof Error) {
            if (error.message.includes('timeout') || error.name === 'TimeoutError') {
            return `Failed to fetch ${url}: The page took too long to load (timeout after 30 seconds).`;
            }
            if (error.message.includes('net::ERR_NAME_NOT_RESOLVED')) {
            return `Failed to fetch ${url}: Domain name could not be resolved.`;
            }
            if (error.message.includes('net::ERR_CONNECTION_REFUSED')) {
            return `Failed to fetch ${url}: Connection was refused by the server.`;
            }
            if (error.message.includes('net::ERR_INTERNET_DISCONNECTED')) {
            return `Failed to fetch ${url}: No internet connection available.`;
            }
        }
        
        return `Failed to fetch content from ${url}: ${error instanceof Error ? error.message : String(error)}`;
        
        } finally {
        // Always cleanup resources
        if (page) {
            try {
            await page.close();
            } catch (closeError) {
            console.error('Error closing page:', closeError);
            }
        }
        if (browser) {
            try {
            await browser.close();
            } catch (closeError) {
            console.error('Error closing browser:', closeError);
            }
        }
        }
    },
}); 