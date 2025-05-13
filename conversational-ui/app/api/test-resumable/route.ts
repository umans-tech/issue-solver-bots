import { NextResponse } from 'next/server';
import { createResumableStreamPublisher, createResumableStreamConsumer } from '@/lib/resumable-stream';

export async function GET() {
  try {
    // Create a test chat ID
    const chatId = 'test-chat-' + Date.now();
    const logs: string[] = [];
    
    logs.push(`Using test chat ID: ${chatId}`);
    
    // 1. Create a resumable stream publisher
    logs.push('Creating resumable stream publisher...');
    const { publisher, streamId } = await createResumableStreamPublisher(chatId);
    
    if (!publisher || !streamId) {
      logs.push('Failed to create publisher or Redis is not available.');
      return NextResponse.json({ success: false, logs });
    }
    
    logs.push(`Stream created with ID: ${streamId}`);
    
    // 2. Append some data to the stream
    logs.push('Appending data to stream...');
    publisher.append({ text: 'Hello' });
    publisher.append({ text: ' world' });
    publisher.append({ text: '!' });
    publisher.close();
    
    // 3. Create a consumer for the same stream
    logs.push('Creating consumer for the stream...');
    const consumer = await createResumableStreamConsumer(streamId);
    
    if (!consumer) {
      logs.push('Failed to create consumer or Redis is not available.');
      return NextResponse.json({ success: false, logs });
    }
    
    // 4. Get all chunks from the stream
    logs.push('Reading chunks from the stream...');
    const chunks = await consumer.getAllChunks();
    
    logs.push('Stream content:');
    let fullText = '';
    for (const chunk of chunks) {
      if (chunk.text) {
        fullText += chunk.text;
        logs.push(`- Chunk: ${chunk.text}`);
      } else {
        logs.push(`- Non-text chunk: ${JSON.stringify(chunk)}`);
      }
    }
    
    logs.push(`\nFull text: "${fullText}"`);
    logs.push('Test completed successfully!');
    
    return NextResponse.json({ 
      success: true,
      chatId,
      streamId,
      fullText,
      logs
    });
  } catch (error) {
    console.error('Error during test:', error);
    return NextResponse.json({ 
      success: false,
      error: error instanceof Error ? error.message : String(error) 
    }, { status: 500 });
  }
}