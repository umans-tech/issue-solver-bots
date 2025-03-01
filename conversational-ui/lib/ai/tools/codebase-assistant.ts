import { z } from 'zod';
import { Session } from 'next-auth';
import { DataStreamWriter, smoothStream, streamText, tool } from 'ai';
import { generateUUID } from '@/lib/utils';
import { myProvider } from '../models';
import fs from 'fs';
import path from 'path';

interface CodebaseAssistantProps {
  session: Session;
  dataStream: DataStreamWriter;
}

export const codebaseAssistant = ({
  session,
  dataStream,
}: CodebaseAssistantProps) =>
  tool({
    description: 'Get help from an AI assistant with knowledge of your codebase or any reference of codebase from the user',
    parameters: z.object({
      query: z
        .string()
        .describe('The question or task related to the codebase'),
      codebase: z
        .string()
        .optional()
        .describe('The name of the codebase to use (if multiple are available)'),
    }),
    execute: async ({ query, codebase }) => {
      // Get the codebase content from the digest.txt file
      const codebaseContent = getCodebaseContent();
      
      if (!codebaseContent) {
        return {
          error: 'Codebase digest file not found or could not be read',
        };
      }

      // Create a system prompt that includes the codebase content
      const systemPrompt = `You are a helpful coding assistant with knowledge of the following codebase. 
Use this knowledge to answer questions and provide assistance.

CODEBASE CONTENT:
${codebaseContent}

Answer questions about this codebase in a helpful, accurate, and concise manner.
Format your response using Markdown for code blocks, headings, and other formatting.
Use syntax highlighting for code blocks by specifying the language.`;

      // Stream the response from the model
      let responseContent = '';
      
      const { fullStream } = streamText({
        model: myProvider.languageModel('codebase-model'),
        system: systemPrompt,
        messages: [{ role: 'user', content: query }],
        experimental_generateMessageId: generateUUID,
        experimental_transform: smoothStream({ chunking: 'word' }),
      });

      // Process the stream and collect the full response
      for await (const delta of fullStream) {
        if (delta.type === 'text-delta') {
          responseContent += delta.textDelta;
        }
      }

      // Return the complete response as a simple string
      return responseContent || 'No response was generated. Please try again.';
    },
  });

// This function reads the codebase content from the digest.txt file in the same directory
function getCodebaseContent(): string | null {
  try {
    // Path to the digest.txt file
    // Using process.cwd() which points to the root of the project
    const digestPath = path.join(process.cwd(), 'lib', 'ai', 'tools', 'digest.txt');
    
    // Check if the file exists
    if (!fs.existsSync(digestPath)) {
      console.error('Digest file not found at:', digestPath);
      return null;
    }
    
    // Read the file
    const digestContent = fs.readFileSync(digestPath, 'utf-8');
    return digestContent;
  } catch (error) {
    console.error('Error reading digest.txt:', error);
    return null;
  }
} 