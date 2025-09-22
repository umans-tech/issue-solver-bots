'use client';

import { SharedHeader } from '@/components/shared-header';

export default function DocsPage() {
  return (
    <div className="flex flex-col min-w-0 h-dvh bg-background">
      <SharedHeader>
        <div className="flex items-center gap-3 text-sm min-w-0">
          <span className="text-lg lg:text-xl font-semibold text-foreground truncate">
            Docs
          </span>
        </div>
      </SharedHeader>
      <div className="flex-1 overflow-auto">
        <div className="container mx-auto py-6 px-4 lg:px-6">
          <div className="border rounded-md p-6 text-center text-muted-foreground">
            No doc available
          </div>
        </div>
      </div>
    </div>
  );
}


