import NextAuth, { DefaultSession } from "next-auth";

declare module "next-auth" {
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
      } | null;
      spaces?: Array<{
        id: string;
        name: string;
        knowledgeBaseId?: string | null;
        processId?: string | null;
        connectedRepoUrl?: string | null;
        isDefault?: boolean;
      }>;
    } & DefaultSession["user"];
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
    } | null;
    spaces?: Array<{
      id: string;
      name: string;
      knowledgeBaseId?: string | null;
      processId?: string | null;
      connectedRepoUrl?: string | null;
      isDefault?: boolean;
    }>;
  }
} 