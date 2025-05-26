import NextAuth, { DefaultSession } from "next-auth";

declare module "next-auth" {
  /**
   * Extend the built-in session types
   */
  interface Session {
    user: {
      id: string;
      selectedSpace?: {
        id: string;
        name: string;
        knowledgeBaseId?: string | null;
        processId?: string | null;
        isDefault?: boolean;
      } | null;
      spaces?: Array<{
        id: string;
        name: string;
        knowledgeBaseId?: string | null;
        processId?: string | null;
        isDefault?: boolean;
      }>;
      // Add additional fields to support social providers
      provider?: string;
      emailVerified?: Date | null;
    } & DefaultSession["user"];
  }

  /**
   * Extend the built-in user types
   */
  interface User {
    id: string;
    selectedSpace?: {
      id: string;
      name: string;
      knowledgeBaseId?: string | null;
      processId?: string | null;
      isDefault?: boolean;
    } | null;
    spaces?: Array<{
      id: string;
      name: string;
      knowledgeBaseId?: string | null;
      processId?: string | null;
      isDefault?: boolean;
    }>;
    // Add additional fields to support social providers and email verification
    provider?: string;
    emailVerified?: Date | null;
  }
}

declare module "next-auth/jwt" {
  /**
   * Extend the built-in JWT types
   */
  interface JWT {
    id: string;
    selectedSpace?: {
      id: string;
      name: string;
      knowledgeBaseId?: string | null;
      processId?: string | null;
      isDefault?: boolean;
    } | null;
    spaces?: Array<{
      id: string;
      name: string;
      knowledgeBaseId?: string | null;
      processId?: string | null;
      isDefault?: boolean;
    }>;
    // Add additional fields to support social providers
    provider?: string;
    emailVerified?: Date | null;
  }
}