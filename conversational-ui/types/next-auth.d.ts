import type { DefaultSession } from 'next-auth';

declare module 'next-auth' {
  interface Session {
    user: {
      id: string;
      selectedSpace?: {
        id: string;
        name: string;
        knowledgeBaseId?: string | null;
        processId?: string | null;
        connectedRepoUrl?: string | null;
        isDefault?: boolean;
        indexedVersions?: Array<{
          sha: string;
          indexedAt?: string;
          branch?: string;
        }> | null;
      } | null;
      spaces?: Array<{
        id: string;
        name: string;
        knowledgeBaseId?: string | null;
        processId?: string | null;
        connectedRepoUrl?: string | null;
        isDefault?: boolean;
        indexedVersions?: Array<{
          sha: string;
          indexedAt?: string;
          branch?: string;
        }> | null;
      }>;
    } & DefaultSession['user'];
  }

  interface User {
    id: string;
    selectedSpace?: {
      id: string;
      name: string;
      knowledgeBaseId?: string | null;
      processId?: string | null;
      connectedRepoUrl?: string | null;
      isDefault?: boolean;
      indexedVersions?: Array<{
        sha: string;
        indexedAt?: string;
        branch?: string;
      }> | null;
    } | null;
    spaces?: Array<{
      id: string;
      name: string;
      knowledgeBaseId?: string | null;
      processId?: string | null;
      connectedRepoUrl?: string | null;
      isDefault?: boolean;
      indexedVersions?: Array<{
        sha: string;
        indexedAt?: string;
        branch?: string;
      }> | null;
    }>;
  }
}
