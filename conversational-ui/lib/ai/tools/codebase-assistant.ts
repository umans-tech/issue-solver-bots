import {z} from 'zod';
import {tool} from 'ai';
import {GetObjectCommand, S3Client} from '@aws-sdk/client-s3';

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

// Map query types to their corresponding S3 file keys base names
// The complete path will be constructed with user-specific space information
const queryTypeToFileBaseMap = {
    codebase_full: 'digest_small.txt',
    adr: 'adrs.txt',
    glossary: 'glossary.txt'
};

export const codebaseAssistant = tool({
    description: 'Retrieve information about the codebase of the current project.',
    parameters: z.object({
        query: QueryTypeEnum.describe(
            'The type of codebase information to retrieve: \n' +
            '- codebase_full: ' + queryTypeDescriptions.codebase_full + '\n' +
            '- adr: ' + queryTypeDescriptions.adr + '\n' +
            '- glossary: ' + queryTypeDescriptions.glossary
        ),
        userId: z.string().optional().describe('The ID of the user requesting the information. If not provided, will use the authenticated user ID.'),
    }),
    execute: async ({query, userId}) => {
        // Use the provided userId or get it from the authenticated user context
        const effectiveUserId = userId || 'current-user'; // Replace with actual user ID retrieval logic
        
        const codebaseContent = await getCodebaseContent(query, effectiveUserId);
        return codebaseContent || 'No response was generated. Please try again.';
    },
});

// This function reads the codebase content from the specified file in the S3 bucket
export async function getCodebaseContent(
    queryType: z.infer<typeof QueryTypeEnum>, 
    userId: string = 'current-user'
): Promise<string | null> {

    // Initialize S3 client with custom endpoint if provided
    const s3Client = new S3Client({
        region: process.env.BLOB_REGION || '',
        endpoint: process.env.BLOB_ENDPOINT || '',
        // Use path-style addressing for non-AWS endpoints
        forcePathStyle: !!process.env.BLOB_ENDPOINT,
        credentials: {
            accessKeyId: process.env.BLOB_ACCESS_KEY_ID || '',
            secretAccessKey: process.env.BLOB_READ_WRITE_TOKEN || '',
        },
    });

    const BUCKET_NAME = process.env.BLOB_BUCKET_NAME || '';

    try {
        // Get the base file name based on the query type
        const baseFileName = queryTypeToFileBaseMap[queryType];
        
        // Construct the full file key with user-specific space
        // Simple and direct mapping of users to spaces
        const fileKey = `spaces/${userId}/${baseFileName}`;

        // Try to get the file from S3
        try {
            const command = new GetObjectCommand({
                Bucket: BUCKET_NAME,
                Key: fileKey,
            });

            const response = await s3Client.send(command);

            // Convert the stream to a string
            if (response.Body) {
                return response.Body.transformToString();
            }

            console.error(`S3 response body is empty for ${fileKey}`);
            return null;
        } catch (s3Error) {
            console.error(`Error fetching ${fileKey} from S3:`, s3Error);
            // No fallback available, return null
            return null;
        }
    } catch (error) {
        console.error(`Error reading file for query type ${queryType}:`, error);
        return null;
    }
}