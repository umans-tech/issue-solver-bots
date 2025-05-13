import { createResumableStreamPublisher, createResumableStreamConsumer } from './lib/resumable-stream';

// Test function to simulate the flow of creating and resuming a stream
async function testResumableStream() {
  try {
    console.log('Testing resumable stream functionality...');
    
    // Create a test chat ID
    const chatId = 'test-chat-' + Date.now();
    console.log(`Using test chat ID: ${chatId}`);
    
    // 1. Create a resumable stream publisher
    console.log('Creating resumable stream publisher...');
    const { publisher, streamId } = await createResumableStreamPublisher(chatId);
    
    if (!publisher || !streamId) {
      console.error('Failed to create publisher or Redis is not available.');
      return;
    }
    
    console.log(`Stream created with ID: ${streamId}`);
    
    // 2. Append some data to the stream
    console.log('Appending data to stream...');
    publisher.append({ text: 'Hello' });
    publisher.append({ text: ' world' });
    publisher.append({ text: '!' });
    publisher.close();
    
    // 3. Create a consumer for the same stream
    console.log('Creating consumer for the stream...');
    const consumer = await createResumableStreamConsumer(streamId);
    
    if (!consumer) {
      console.error('Failed to create consumer or Redis is not available.');
      return;
    }
    
    // 4. Get all chunks from the stream
    console.log('Reading chunks from the stream...');
    const chunks = await consumer.getAllChunks();
    
    console.log('Stream content:');
    let fullText = '';
    for (const chunk of chunks) {
      if (chunk.text) {
        fullText += chunk.text;
        console.log(`- Chunk: ${chunk.text}`);
      } else {
        console.log(`- Non-text chunk: ${JSON.stringify(chunk)}`);
      }
    }
    
    console.log(`\nFull text: "${fullText}"`);
    console.log('Test completed successfully!');
    
  } catch (error) {
    console.error('Error during test:', error);
  }
}

// Run the test
testResumableStream();