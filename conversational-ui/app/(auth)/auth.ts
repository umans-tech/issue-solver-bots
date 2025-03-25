import { compare } from 'bcrypt-ts';
import NextAuth, { type User, type Session } from 'next-auth';
import Credentials from 'next-auth/providers/credentials';

import { getUser, getSelectedSpace } from '@/lib/db/queries';

import { authConfig } from './auth.config';

interface ExtendedSession extends Session {
  user: {
    id: string;
    selectedSpace?: {
      id: string;
      name: string;
      knowledgeBaseId?: string | null;
      processId?: string | null;
      isDefault?: boolean;
    } | null;
  } & Omit<Session['user'], 'id'>;
}

export const {
  handlers: { GET, POST },
  auth,
  signIn,
  signOut,
} = NextAuth({
  ...authConfig,
  providers: [
    Credentials({
      credentials: {},
      async authorize({ email, password }: any) {
        const users = await getUser(email);
        if (users.length === 0) return null;
        // biome-ignore lint: Forbidden non-null assertion.
        const passwordsMatch = await compare(password, users[0].password!);
        if (!passwordsMatch) return null;
        return users[0] as any;
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
      }
        
      // Always get the user's selected space directly from the database
      // This ensures we always have the latest data, even during token refreshes
      if (token.id) {
        const selectedSpace = await getSelectedSpace(token.id as string);
        if (selectedSpace) {
          console.log("JWT refresh: Getting latest space data from database:", {
            id: selectedSpace.id,
            knowledgeBaseId: selectedSpace.knowledgeBaseId,
            processId: selectedSpace.processId
          });
          
          token.selectedSpace = {
            id: selectedSpace.id,
            name: selectedSpace.name,
            knowledgeBaseId: selectedSpace.knowledgeBaseId,
            processId: selectedSpace.processId,
            isDefault: selectedSpace.isDefault,
          };
        }
      }

      return token;
    },
    async session({
      session,
      token,
    }: {
      session: ExtendedSession;
      token: any;
    }) {
      if (session.user) {
        session.user.id = token.id as string;
        
        // Add selected space info to the session
        if (token.selectedSpace) {
          session.user.selectedSpace = {
            id: token.selectedSpace.id,
            name: token.selectedSpace.name,
            knowledgeBaseId: token.selectedSpace.knowledgeBaseId,
            processId: token.selectedSpace.processId,
            // Ensure we're passing all properties from the token
            ...(token.selectedSpace.isDefault !== undefined ? { isDefault: token.selectedSpace.isDefault } : {})
          };
          
          // Add an extra check to directly query the database if any critical fields are missing
          // This helps ensure we always have the latest data, especially after repository connection
          const shouldFetchFromDb = 
            token.selectedSpace.knowledgeBaseId === undefined ||
            token.selectedSpace.processId === undefined;
            
          if (shouldFetchFromDb && token.id) {
            try {
              // Double-check with the database to ensure we have the latest
              const spaceFromDb = await getSelectedSpace(token.id as string);
              
              if (spaceFromDb && 
                (spaceFromDb.knowledgeBaseId || spaceFromDb.processId)) {
                
                console.log("Session: Found extra space data in database, updating session:", {
                  id: spaceFromDb.id,
                  knowledgeBaseId: spaceFromDb.knowledgeBaseId,
                  processId: spaceFromDb.processId
                });
                
                // Override with database values if they're more complete
                session.user.selectedSpace = {
                  ...session.user.selectedSpace,
                  knowledgeBaseId: spaceFromDb.knowledgeBaseId,
                  processId: spaceFromDb.processId
                };
              }
            } catch (error) {
              console.error("Error fetching space data in session callback:", error);
            }
          }
          
          // Log to debug session update
          console.log("Session updated with space data:", {
            id: session.user.selectedSpace.id,
            knowledgeBaseId: session.user.selectedSpace.knowledgeBaseId,
            processId: session.user.selectedSpace.processId
          });
        }
      }

      return session;
    },
  },
});
