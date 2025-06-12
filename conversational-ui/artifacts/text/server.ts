import { createDocumentHandler } from '@/lib/artifacts/server';

export const textDocumentHandler = createDocumentHandler<'text'>({
  kind: 'text',
  onCreateDocument: async ({ content, dataStream }) => {
    // Stream the provided content directly without AI generation
    // Split content into chunks for streaming effect
    const words = content.split(' ');
    let streamedContent = '';
    
    for (const word of words) {
      const chunk = streamedContent ? ' ' + word : word;
      streamedContent += chunk;
      
      dataStream.writeData({
        type: 'text-delta',
        content: chunk,
      });
      
      // Small delay to simulate streaming
      await new Promise(resolve => setTimeout(resolve, 10));
    }

    return content;
  },
  onUpdateDocument: async ({ document, searchText, replaceText }) => {
    const currentContent = document.content || '';

    // Check if search text exists in the document
    if (!currentContent.includes(searchText)) {
      return {
        success: false,
        error: `Could not find exact match for: "${searchText}". Please check the text and try again.`,
      };
    }

    // Replacement is done by the wrapper; nothing to stream here – we want to show the full updated document once it's saved.
    return {
      success: true,
    };
  },
});
