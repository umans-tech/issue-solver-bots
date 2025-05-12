import { z } from "zod";
import { Session } from "next-auth";
import { tool } from "ai";
import { DataStreamWriter } from "ai";

interface RemoteCodingAgentProps {
    session: Session;
    dataStream: DataStreamWriter;
}

const issueSchema = z.object({
    description: z.string().describe('The description of the issue to be resolved.'),
    title: z.string().optional().describe('The title of the issue to be resolved.'),
});

export const remoteCodingAgent = ({ session }: RemoteCodingAgentProps) => tool({
    description: "A tool for that launch a remote instance of a coding agent to resolve an issue by submitting a PR/MR.",
    parameters: z.object({
        issue: issueSchema,
    }),
    execute: async ({ issue }) => {
        try {
            // @ts-ignore - Accessing properties that TypeScript doesn't know about
            const knowledgeBaseId = session.knowledgeBaseId ||
                             session?.user?.selectedSpace?.knowledgeBaseId;

            if (!knowledgeBaseId) {
                return 'No knowledge base found for this user. Please connect a repository first.';
            }

            // Get the CUDU API endpoint from environment variables
            const cuduEndpoint = process.env.CUDU_ENDPOINT;

            if (!cuduEndpoint) {
                return 'CUDU API endpoint is not configured';
            }

            // Prepare the request body
            const requestBody = {
                knowledgeBaseId,
                issue,
            };

            // Send request to CUDU API
            const response = await fetch(`${cuduEndpoint}/resolutions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                const errorData = await response.json();
                console.error('Error from CUDU API:', errorData);
                return `Failed to create resolution: ${errorData.detail || response.statusText}`;
            }

            const data = await response.json();
            return data;
            

        } catch (error) {
            console.error("Error in remote coding agent:", error);
            return "An error occurred while processing the issue.";
        }
    },
});

