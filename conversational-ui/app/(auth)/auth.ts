import { compare } from 'bcrypt-ts';
import NextAuth, { type Session } from 'next-auth';
import Credentials from 'next-auth/providers/credentials';
import Google from 'next-auth/providers/google';

import {
  getUser,
  getSelectedSpace,
  createUser,
  ensureDefaultSpace,
  verifyUserEmail,
  updateUserProfile,
} from '@/lib/db/queries';

import { authConfig } from './auth.config';

interface ExtendedSession extends Session {
  user: {
    id: string;
    hasCompletedOnboarding?: boolean;
    selectedSpace?: {
      id: string;
      name: string;
      knowledgeBaseId?: string | null;
      processId?: string | null;
      connectedRepoUrl?: string | null;
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
    Google({
      clientId: process.env.AUTH_GOOGLE_ID,
      clientSecret: process.env.AUTH_GOOGLE_SECRET,
    }),
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null;
        }
        
        const email = credentials.email as string;
        const password = credentials.password as string;
        
        const users = await getUser(email);
        if (users.length === 0) return null;

        // Check if user has a password (not an OAuth user)
        if (!users[0].password) return null;

        // Check if email is verified
        if (!users[0].emailVerified) {
          return null; // Reject unverified users
        }

        // biome-ignore lint: Forbidden non-null assertion.
        const passwordsMatch = await compare(password, users[0].password!);
        if (!passwordsMatch) return null;
        return users[0] as any;
      },
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      console.log('🔐 NextAuth signIn callback triggered', {
        provider: account?.provider,
        userEmail: user?.email,
        userId: user?.id
      });

      if (account?.provider === 'google') {
        try {
          console.log('🔍 Checking if Google user exists:', user.email);
          
          const existingUsers = await getUser(user.email!);
          console.log('👤 Existing users found:', existingUsers.length);
          
          if (existingUsers.length === 0) {
            console.log('➕ Creating new OAuth user:', user.email);
            
            await createUser(user.email!, null, user.name, user.image);
            console.log('✅ User created successfully');
            
            await new Promise(resolve => setTimeout(resolve, 100));

            const [newUser] = await getUser(user.email!);
            if (newUser?.id) {
              await verifyUserEmail(newUser.id);
              console.log('✅ OAuth user email verified automatically');
            }
          } else {
            const dbUser = existingUsers[0];
            if (!dbUser.name || !dbUser.image) {
              await updateUserProfile(dbUser.id, {
                name: user.name,
                image: user.image
              });
              console.log('✅ Updated existing user profile with Google data');
            }
          }
          
          const [dbUser] = await getUser(user.email!);
          console.log('👤 Database user retrieved:', dbUser?.id);
          
          if (!dbUser?.id) {
            console.error('❌ Failed to retrieve user from database');
            return false;
          }
          
          console.log('🏠 Creating default space for database user:', dbUser.id);
          try {
            await ensureDefaultSpace(dbUser.id);
            console.log('✅ Default space created successfully');
          } catch (spaceError) {
            console.error('❌ Error creating default space:', spaceError);
            console.log('⚠️ Continuing with sign-in despite space creation failure');
          }
          
          console.log('🎉 Google OAuth sign-in successful');
          return true;
        } catch (error) {
          console.error('❌ Error in Google OAuth signIn callback:', error);
          return false;
        }
      }
      
      console.log('✅ Non-Google sign-in successful');
      return true;
    },
    async jwt({ token, user }) {
      if (user) {
        const [dbUser] = await getUser(user.email!);
        if (dbUser?.id) {
          token.id = dbUser.id;
          token.hasCompletedOnboarding = dbUser.hasCompletedOnboarding;
        } else {
          console.error('❌ JWT: Could not find database user for email:', user.email);
          token.id = user.id;
        }
      }
        
      // Always refresh hasCompletedOnboarding from database for existing tokens
      if (token.id && token.email) {
        const [dbUser] = await getUser(token.email as string);
        if (dbUser) {
          token.hasCompletedOnboarding = dbUser.hasCompletedOnboarding;
        }
      }

      if (token.id) {
        const selectedSpace = await getSelectedSpace(token.id as string);
        if (selectedSpace) {
          token.selectedSpace = {
            id: selectedSpace.id,
            name: selectedSpace.name,
            knowledgeBaseId: selectedSpace.knowledgeBaseId,
            processId: selectedSpace.processId,
            connectedRepoUrl: selectedSpace.connectedRepoUrl,
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
      token: Record<string, any>;
    }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.hasCompletedOnboarding = token.hasCompletedOnboarding as boolean;

        // Add selected space info to the session
        if (token.selectedSpace) {
          session.user.selectedSpace = {
            id: token.selectedSpace.id,
            name: token.selectedSpace.name,
            knowledgeBaseId: token.selectedSpace.knowledgeBaseId,
            processId: token.selectedSpace.processId,
            connectedRepoUrl: token.selectedSpace.connectedRepoUrl,
            // Ensure we're passing all properties from the token
            ...(token.selectedSpace.isDefault !== undefined
              ? { isDefault: token.selectedSpace.isDefault }
              : {}),
          };

          // Add an extra check to directly query the database if any critical fields are missing
          // This helps ensure we always have the latest data, especially after repository connection
          const shouldFetchFromDb =
            token.selectedSpace.knowledgeBaseId === undefined ||
            token.selectedSpace.processId === undefined ||
            token.selectedSpace.connectedRepoUrl === undefined;

          if (shouldFetchFromDb && token.id) {
            try {
              // Double-check with the database to ensure we have the latest
              const spaceFromDb = await getSelectedSpace(token.id as string);

              if (
                spaceFromDb &&
                (spaceFromDb.knowledgeBaseId || spaceFromDb.processId || spaceFromDb.connectedRepoUrl)
              ) {
                console.log(
                  'Session: Found extra space data in database, updating session:',
                  {
                    id: spaceFromDb.id,
                    knowledgeBaseId: spaceFromDb.knowledgeBaseId,
                    processId: spaceFromDb.processId,
                    connectedRepoUrl: spaceFromDb.connectedRepoUrl,
                  },
                );

                // Override with database values if they're more complete
                session.user.selectedSpace = {
                  ...session.user.selectedSpace,
                  knowledgeBaseId: spaceFromDb.knowledgeBaseId,
                  processId: spaceFromDb.processId,
                  connectedRepoUrl: spaceFromDb.connectedRepoUrl,
                };
              }
            } catch (error) {
              console.error(
                'Error fetching space data in session callback:',
                error,
              );
            }
          }

          // Log to debug session update
          console.log('Session updated with space data:', {
            id: session.user.selectedSpace.id,
            knowledgeBaseId: session.user.selectedSpace.knowledgeBaseId,
            processId: session.user.selectedSpace.processId,
            connectedRepoUrl: session.user.selectedSpace.connectedRepoUrl,
          });
        }
      }

      return session;
    },
  },
});
