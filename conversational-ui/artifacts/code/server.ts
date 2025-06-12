import { z } from 'zod';
import { streamObject } from 'ai';
import { myProvider } from '@/lib/ai/models';
import { codePrompt } from '@/lib/ai/prompts';
import { createDocumentHandler } from '@/lib/artifacts/server';

export const codeDocumentHandler = createDocumentHandler<'code'>({
  kind: 'code',
  onCreateDocument: async ({ title, dataStream }) => {
    let draftContent = '';

    const { fullStream } = streamObject({
      model: myProvider.languageModel('artifact-model'),
      system: codePrompt,
      prompt: title,
      schema: z.object({
        code: z.string(),
      }),
    });

    for await (const delta of fullStream) {
      const { type } = delta;

      if (type === 'object') {
        const { object } = delta;
        const { code } = object;

        if (code) {
          dataStream.writeData({
            type: 'code-delta',
            content: code ?? '',
          });

          draftContent = code;
        }
      }
    }

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

    // Stream full updated content as a single delta
    dataStream.writeData({
      type: 'code-delta',
      content: updatedContent,
    });

    return {
      success: true,
    };
  },
});
