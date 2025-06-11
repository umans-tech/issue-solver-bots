import { DataStreamWriter, tool } from 'ai';
import { Session } from 'next-auth';
import { z } from 'zod';
import { getDocumentById, saveDocument } from '@/lib/db/queries';
import { documentHandlersByArtifactKind } from '@/lib/artifacts/server';

interface UpdateDocumentProps {
  session: Session;
  dataStream: DataStreamWriter;
}

export const updateDocument = ({ session, dataStream }: UpdateDocumentProps) =>
  tool({
    description: 'Update a document using search and replace functionality. Find exact text and replace it with new text.',
    parameters: z.object({
      id: z.string().describe('The ID of the document to update'),
      searchText: z.string().describe('The exact text block to find in the document'),
      replaceText: z.string().describe('The text to replace the found block with'),
    }),
    execute: async ({ id, searchText, replaceText }) => {
      const document = await getDocumentById({ id });

      if (!document) {
        return {
          error: 'Document not found',
        };
      }

      dataStream.writeData({
        type: 'clear',
        content: document.title,
      });

      const documentHandler = documentHandlersByArtifactKind.find(
        (documentHandlerByArtifactKind) =>
          documentHandlerByArtifactKind.kind === document.kind,
      );

      if (!documentHandler) {
        throw new Error(`No document handler found for kind: ${document.kind}`);
      }

      const result = await documentHandler.onUpdateDocument({
        document,
        searchText,
        replaceText,
        dataStream,
        session,
      });

      dataStream.writeData({ type: 'finish', content: '' });

      if (result.success) {
        return {
          id,
          title: document.title,
          kind: document.kind,
          content: 'The document has been updated successfully.',
        };
      } else {
        return {
          id,
          title: document.title,
          kind: document.kind,
          content: result.error || 'Failed to update document.',
          error: result.error,
        };
      }
    },
  });
