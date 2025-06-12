import { myProvider } from '@/lib/ai/models';
import { sheetPrompt } from '@/lib/ai/prompts';
import { createDocumentHandler } from '@/lib/artifacts/server';
import { streamObject } from 'ai';
import { z } from 'zod';

export const sheetDocumentHandler = createDocumentHandler<'sheet'>({
  kind: 'sheet',
  onCreateDocument: async ({ title, dataStream }) => {
    let draftContent = '';

    const { fullStream } = streamObject({
      model: myProvider.languageModel('artifact-model'),
      system: sheetPrompt,
      prompt: title,
      schema: z.object({
        csv: z.string().describe('CSV data'),
      }),
    });

    for await (const delta of fullStream) {
      const { type } = delta;

      if (type === 'object') {
        const { object } = delta;
        const { csv } = object;

        if (csv) {
          dataStream.writeData({
            type: 'sheet-delta',
            content: csv,
          });

          draftContent = csv;
        }
      }
    }

    dataStream.writeData({
      type: 'sheet-delta',
      content: draftContent,
    });

    return draftContent;
  },
  onUpdateDocument: async ({ document, searchText, replaceText, dataStream }) => {
    const currentContent = document.content || '';

    if (!currentContent.includes(searchText)) {
      return {
        success: false,
        error: `Could not find exact match for: "${searchText}". Please check the text and try again.`,
      };
    }

    const updatedContent = currentContent.replace(searchText, replaceText);

    dataStream.writeData({
      type: 'sheet-delta',
      content: updatedContent,
    });

    return {
      success: true,
    };
  },
});
