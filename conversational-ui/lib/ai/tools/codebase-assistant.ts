import { z } from 'zod';
import { tool } from 'ai';
import { S3Client, GetObjectCommand } from '@aws-sdk/client-s3';


// Initialize S3 client
const s3Client = new S3Client({
  region: process.env.AWS_REGION || '',
  endpoint: process.env.AWS_ENDPOINT || '',
  forcePathStyle: true,
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || '',
  },
});

const BUCKET_NAME = process.env.S3_BUCKET_NAME || '';

// Define the query type enum with detailed descriptions
const QueryTypeEnum = z.enum([
  'codebase_full',
  'adr',
  'glossary'
]);

// Descriptions for each query type
const queryTypeDescriptions = {
  codebase_full: 'Returns the complete content of the codebase, including all files, directories, and their contents.',
  adr: 'Returns Architectural Decision Records (ADRs), coding guidelines, and standards that govern the development of the codebase.',
  glossary: 'Returns the Ubiquitous Language Glossary that maps technical code terms to business concept terms, facilitating consistent understanding across technical and domain contexts.'
};

// Map query types to their corresponding S3 file keys
const queryTypeToFileMap = {
  codebase_full: 'digest_small.txt',
  adr: 'adrs.txt',
  glossary: 'glossary.txt'
};

export const codebaseAssistant = tool({
  description: 'Retrieve information about the codebase of the current project.',
  parameters: z.object({
      query: QueryTypeEnum
        .describe('The type of codebase information to retrieve: \n' +
          '- codebase_full: ' + queryTypeDescriptions.codebase_full + '\n' +
          '- adr: ' + queryTypeDescriptions.adr + '\n' +
          '- glossary: ' + queryTypeDescriptions.glossary),
    }),
    execute: async ({ query }) => {
      const codebaseContent = await getCodebaseContent(query);
      return codebaseContent || 'No response was generated. Please try again.';
    },
  });

// This function reads the codebase content from the specified file in the S3 bucket
export async function getCodebaseContent(queryType: z.infer<typeof QueryTypeEnum>): Promise<string | null> {
  try {
    // Get the file key based on the query type
    const fileKey = queryTypeToFileMap[queryType];
    
    // Try to get the file from S3
    try {
      const command = new GetObjectCommand({
        Bucket: BUCKET_NAME,
        Key: fileKey,
      });
      
      const response = await s3Client.send(command);
      
      // Convert the stream to a string
      if (response.Body) {
        const streamReader = response.Body.transformToString();
        return streamReader;
      }
      
      console.error(`S3 response body is empty for ${fileKey}`);
      return null;
    } catch (s3Error) {
      console.error(`Error fetching ${fileKey} from S3:`, s3Error);
      // No fallback available, return null
      console.error(`Unable to fetch ${fileKey} from S3`);
      return null;
    }
  } catch (error) {
    console.error(`Error reading file for query type ${queryType}:`, error);
    return null;
  }
} 