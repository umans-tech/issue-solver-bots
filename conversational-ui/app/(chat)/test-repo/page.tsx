'use client';

import { ChatRepoConnection } from '@/components/chat-repo-connection';

export default function TestRepoPage() {
  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-start justify-end p-4">
      <ChatRepoConnection
        onConnectionStart={() => console.log('Connection started')}
        onConnectionComplete={(success, details) => {
          console.log('Connection completed:', { success, details });
        }}
        onStatusUpdate={(status, message) => {
          console.log('Status update:', { status, message });
        }}
      />
    </div>
  );
} 