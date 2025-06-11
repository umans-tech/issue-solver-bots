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
      await new Promise(resolve => setTimeout(resolve, 50));
    }

    return content;
  },
  onUpdateDocument: async ({ document, searchText, replaceText, dataStream }) => {
    const currentContent = document.content || '';
    
    // Check if search text exists in the document
    if (!currentContent.includes(searchText)) {
      return {
        success: false,
        error: `Could not find exact match for: "${searchText}". Please check the text and try again.`,
      };
    }
    
    // Perform the replacement
    const updatedContent = currentContent.replace(searchText, replaceText);
    
    // Stream the replacement text
    const words = replaceText.split(' ');
    for (const word of words) {
      const chunk = words.indexOf(word) === 0 ? word : ' ' + word;
      
      dataStream.writeData({
        type: 'text-delta',
        content: chunk,
      });
      
      // Small delay to simulate streaming
      await new Promise(resolve => setTimeout(resolve, 50));
    }
    
    return {
      success: true,
    };
  },
});
