import 'server-only';

import { genSaltSync, hashSync } from 'bcrypt-ts';
import { and, asc, desc, eq, gt, gte, inArray, sql } from 'drizzle-orm';
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';

import {
  user,
  chat,
  type User,
  document,
  type Suggestion,
  suggestion,
  type DBMessage,
  message,
  vote,
  space,
  spaceToUser,
  stream,
  tokenUsage,
  type TokenUsage,
} from './schema';
import { ArtifactKind } from '@/components/artifact';

// Optionally, if not using email/pass login, you can
// use the Drizzle adapter for Auth.js / NextAuth
// https://authjs.dev/reference/adapter/drizzle

// biome-ignore lint: Forbidden non-null assertion.
const client = postgres(process.env.POSTGRES_URL!);
const db = drizzle(client);

export async function getUser(email: string): Promise<Array<User>> {
  try {
    return await db.select().from(user).where(eq(user.email, email));
  } catch (error) {
    console.error('Failed to get user from database');
    throw error;
  }
}

export async function createUser(
  email: string, 
  password: string | null, 
  name?: string | null, 
  image?: string | null
) {
  let hash = null;
  if (password) {
    const salt = genSaltSync(10);
    hash = hashSync(password, salt);
  }

  try {
    return await db.insert(user).values({ email, password: hash, name, image });
  } catch (error) {
    console.error('Failed to create user in database');
    throw error;
  }
}

export async function createUserWithVerification(
  email: string, 
  password: string, 
  verificationToken: string
) {
  const salt = genSaltSync(10);
  const hash = hashSync(password, salt);

  try {
    return await db.insert(user).values({ 
      email, 
      password: hash, 
      emailVerificationToken: verificationToken
    });
  } catch (error) {
    console.error('Failed to create user with verification in database');
    throw error;
  }
}

export async function getUserByVerificationToken(token: string): Promise<Array<User>> {
  try {
    return await db.select().from(user).where(eq(user.emailVerificationToken, token));
  } catch (error) {
    console.error('Failed to get user by verification token from database');
    throw error;
  }
}

export async function verifyUserEmail(userId: string) {
  try {
    const result = await db
      .update(user)
      .set({ 
        emailVerified: new Date(),
        emailVerificationToken: null 
      })
      .where(eq(user.id, userId))
      .returning({ email: user.email });

    // Send welcome email after successful verification
    if (result.length > 0) {
      try {
        const { sendWelcomeEmail } = await import('../email');
        await sendWelcomeEmail(result[0].email);
        console.log('📧 Welcome email sent to verified user:', result[0].email);
      } catch (emailError) {
        console.error('❌ Error sending welcome email:', emailError);
        // Don't fail the verification if welcome email fails
      }
    }

    return result;
  } catch (error) {
    console.error('Failed to verify user email in database');
    throw error;
  }
}

export async function saveChat({
  id,
  userId,
  title,
  spaceId,
}: {
  id: string;
  userId: string;
  title: string;
  spaceId: string;
}) {
  try {
    return await db.insert(chat).values({
      id,
      createdAt: new Date(),
      userId,
      title,
      spaceId,
    });
  } catch (error) {
    console.error('Failed to save chat in database');
    throw error;
  }
}

export async function deleteChatById({ id }: { id: string }) {
  try {
    await db.delete(vote).where(eq(vote.chatId, id));
    await db.delete(tokenUsage).where(eq(tokenUsage.chatId, id));
    await db.delete(message).where(eq(message.chatId, id));
    await db.delete(stream).where(eq(stream.chatId, id));

    return await db.delete(chat).where(eq(chat.id, id));
  } catch (error) {
    console.error('Failed to delete chat by id from database');
    throw error;
  }
}

export async function getChatsByUserId({ id }: { id: string }) {
  try {
    return await db
      .select()
      .from(chat)
      .where(eq(chat.userId, id))
      .orderBy(desc(chat.createdAt));
  } catch (error) {
    console.error('Failed to get chats by user from database');
    throw error;
  }
}

export async function getChatsByUserIdAndSpaceId({ 
  userId, 
  spaceId 
}: { 
  userId: string;
  spaceId: string;
}) {
  try {
    return await db
      .select()
      .from(chat)
      .where(and(eq(chat.userId, userId), eq(chat.spaceId, spaceId)))
      .orderBy(desc(chat.createdAt));
  } catch (error) {
    console.error('Failed to get chats by user and space from database');
    throw error;
  }
}

export async function getChatById({ id }: { id: string }) {
  try {
    const [selectedChat] = await db.select().from(chat).where(eq(chat.id, id));
    return selectedChat;
  } catch (error) {
    console.error('Failed to get chat by id from database');
    throw error;
  }
}

export async function saveMessages({
  messages,
}: { messages: Array<DBMessage> }) {
  try {
    return await db.insert(message).values(messages);
  } catch (error) {
    console.error('Failed to save messages in database', error);
    throw error;
  }
}

export async function getMessagesByChatId({ id }: { id: string }) {
  try {
    return await db
      .select()
      .from(message)
      .where(eq(message.chatId, id))
      .orderBy(asc(message.createdAt));
  } catch (error) {
    console.error('Failed to get messages by chat id from database', error);
    throw error;
  }
}

export async function voteMessage({
  chatId,
  messageId,
  type,
}: {
  chatId: string;
  messageId: string;
  type: 'up' | 'down';
}) {
  try {
    const [existingVote] = await db
      .select()
      .from(vote)
      .where(and(eq(vote.messageId, messageId)));

    if (existingVote) {
      return await db
        .update(vote)
        .set({ isUpvoted: type === 'up' })
        .where(and(eq(vote.messageId, messageId), eq(vote.chatId, chatId)));
    }
    return await db.insert(vote).values({
      chatId,
      messageId,
      isUpvoted: type === 'up',
    });
  } catch (error) {
    console.error('Failed to upvote message in database', error);
    throw error;
  }
}

export async function getVotesByChatId({ id }: { id: string }) {
  try {
    return await db.select().from(vote).where(eq(vote.chatId, id));
  } catch (error) {
    console.error('Failed to get votes by chat id from database', error);
    throw error;
  }
}

export async function saveDocument({
  id,
  title,
  kind,
  content,
  userId,
}: {
  id: string;
  title: string;
  kind: ArtifactKind;
  content: string;
  userId: string;
}) {
  try {
    return await db.insert(document).values({
      id,
      title,
      kind,
      content,
      userId,
      createdAt: new Date(),
    });
  } catch (error) {
    console.error('Failed to save document in database');
    throw error;
  }
}

export async function getDocumentsById({ id }: { id: string }) {
  try {
    const documents = await db
      .select()
      .from(document)
      .where(eq(document.id, id))
      .orderBy(asc(document.createdAt));

    return documents;
  } catch (error) {
    console.error('Failed to get document by id from database');
    throw error;
  }
}

export async function getDocumentById({ id }: { id: string }) {
  try {
    const [selectedDocument] = await db
      .select()
      .from(document)
      .where(eq(document.id, id))
      .orderBy(desc(document.createdAt));

    return selectedDocument;
  } catch (error) {
    console.error('Failed to get document by id from database');
    throw error;
  }
}

export async function deleteDocumentsByIdAfterTimestamp({
  id,
  timestamp,
}: {
  id: string;
  timestamp: Date;
}) {
  try {
    await db
      .delete(suggestion)
      .where(
        and(
          eq(suggestion.documentId, id),
          gt(suggestion.documentCreatedAt, timestamp),
        ),
      );

    return await db
      .delete(document)
      .where(and(eq(document.id, id), gt(document.createdAt, timestamp)));
  } catch (error) {
    console.error(
      'Failed to delete documents by id after timestamp from database',
    );
    throw error;
  }
}

export async function saveSuggestions({
  suggestions,
}: {
  suggestions: Array<Suggestion>;
}) {
  try {
    return await db.insert(suggestion).values(suggestions);
  } catch (error) {
    console.error('Failed to save suggestions in database');
    throw error;
  }
}

export async function getSuggestionsByDocumentId({
  documentId,
}: {
  documentId: string;
}) {
  try {
    return await db
      .select()
      .from(suggestion)
      .where(and(eq(suggestion.documentId, documentId)));
  } catch (error) {
    console.error(
      'Failed to get suggestions by document version from database',
    );
    throw error;
  }
}

export async function getMessageById({ id }: { id: string }) {
  try {
    return await db.select().from(message).where(eq(message.id, id));
  } catch (error) {
    console.error('Failed to get message by id from database');
    throw error;
  }
}

export async function deleteMessagesByChatIdAfterTimestamp({
  chatId,
  timestamp,
}: {
  chatId: string;
  timestamp: Date;
}) {
  try {
    const messagesToDelete = await db
      .select({ id: message.id })
      .from(message)
      .where(
        and(eq(message.chatId, chatId), gte(message.createdAt, timestamp)),
      );

    const messageIds = messagesToDelete.map((message) => message.id);

    if (messageIds.length > 0) {
      await db
        .delete(vote)
        .where(
          and(eq(vote.chatId, chatId), inArray(vote.messageId, messageIds)),
        );

      return await db
        .delete(message)
        .where(
          and(eq(message.chatId, chatId), inArray(message.id, messageIds)),
        );
    }
  } catch (error) {
    console.error(
      'Failed to delete messages by id after timestamp from database',
    );
    throw error;
  }
}

export async function updateChatVisiblityById({
  chatId,
  visibility,
}: {
  chatId: string;
  visibility: 'private' | 'public';
}) {
  try {
    return await db.update(chat).set({ visibility }).where(eq(chat.id, chatId));
  } catch (error) {
    console.error('Failed to update chat visibility in database');
    throw error;
  }
}

export async function updateChatTitleById({
  chatId,
  title,
}: {
  chatId: string;
  title: string;
}) {
  try {
    return await db.update(chat).set({ title }).where(eq(chat.id, chatId));
  } catch (error) {
    console.error('Failed to update chat title in database');
    throw error;
  }
}

// Space-related queries

/**
 * Create a new space for a user
 */
export async function createSpace(
  name: string,
  userId: string,
  knowledgeBaseId?: string,
  processId?: string,
  isDefault: boolean = false,
) {
  try {
    // First verify the user exists
    const userExists = await db
      .select({ id: user.id })
      .from(user)
      .where(eq(user.id, userId))
      .limit(1);

    if (userExists.length === 0) {
      throw new Error(`User with ID ${userId} does not exist`);
    }

    // Create the space
    const newSpaces = await db
      .insert(space)
      .values({
        name,
        knowledgeBaseId,
        processId,
        isDefault,
        createdAt: new Date(),
        updatedAt: new Date(),
      })
      .returning();

    if (newSpaces.length > 0) {
      const newSpace = newSpaces[0];
      
      // Create the space-user relationship
      await db.insert(spaceToUser).values({
        spaceId: newSpace.id,
        userId: userId,
      });
      
      console.log(`✅ Created space "${name}" for user ${userId}`);
      return newSpace;
    }
    
    return null;
  } catch (error) {
    console.error('❌ Error creating space:', error);
    throw error;
  }
}

/**
 * Get all spaces for a user
 */
export async function getSpacesForUser(userId: string) {
  return db
    .select({
      id: space.id,
      name: space.name,
      knowledgeBaseId: space.knowledgeBaseId,
      processId: space.processId,
      connectedRepoUrl: space.connectedRepoUrl,
      createdAt: space.createdAt,
      updatedAt: space.updatedAt,
      isDefault: space.isDefault,
    })
    .from(space)
    .innerJoin(spaceToUser, eq(space.id, spaceToUser.spaceId))
    .where(eq(spaceToUser.userId, userId))
    .orderBy(desc(space.updatedAt));
}

/**
 * Get a space by ID
 */
export async function getSpaceById(spaceId: string) {
  return db
    .select()
    .from(space)
    .where(eq(space.id, spaceId))
    .then((spaces) => spaces[0] || null);
}

/**
 * Update a space's details
 */
export async function updateSpace(
  spaceId: string,
  updates: {
    name?: string;
    knowledgeBaseId?: string;
    processId?: string;
    connectedRepoUrl?: string;
    isDefault?: boolean;
  },
) {
  return db
    .update(space)
    .set({
      ...updates,
      updatedAt: new Date(),
    })
    .where(eq(space.id, spaceId))
    .returning()
    .then((spaces) => spaces[0] || null);
}

/**
 * Set a space as the user's selected space
 */
export async function setSelectedSpace(userId: string, spaceId: string) {
  return db
    .update(user)
    .set({
      selectedSpaceId: spaceId,
    })
    .where(eq(user.id, userId))
    .returning();
}

/**
 * Get the currently selected space for a user
 */
export async function getSelectedSpace(userId: string) {
  return db
    .select({
      selectedSpaceId: user.selectedSpaceId,
    })
    .from(user)
    .where(eq(user.id, userId))
    .then(async (users) => {
      if (users.length > 0 && users[0].selectedSpaceId) {
        return getSpaceById(users[0].selectedSpaceId);
      }
      return null;
    });
}

/**
 * Create a default space for a user if they don't have one
 */
export async function ensureDefaultSpace(userId: string) {
  // Check if user already has a space
  const userSpaces = await getSpacesForUser(userId);

  if (userSpaces.length === 0) {
    // Create a default space for the user
    const defaultSpace = await createSpace(
      'Default Space',
      userId,
      undefined,
      undefined,
      true,
    );

    // Set this as the selected space
    if (defaultSpace) {
      await setSelectedSpace(userId, defaultSpace.id);
      return defaultSpace;
    }
  } else {
    // If user has spaces but none selected, select the most recently updated one
    const userWithSpace = await db
      .select({
        selectedSpaceId: user.selectedSpaceId,
      })
      .from(user)
      .where(eq(user.id, userId))
      .then((users) => users[0]);

    if (!userWithSpace.selectedSpaceId) {
      await setSelectedSpace(userId, userSpaces[0].id);
      return userSpaces[0];
    }

    // Return the currently selected space
    return getSpaceById(userWithSpace.selectedSpaceId);
  }

  return null;
}

export async function createStreamId({
  streamId,
  chatId,
}: {
  streamId: string;
  chatId: string;
}) {
  try {
    await db
      .insert(stream)
      .values({ id: streamId, chatId, createdAt: new Date() });
  } catch (error) {
    console.error('Failed to create stream id in database');
    throw error;
  }
}

export async function getStreamIdsByChatId({ chatId }: { chatId: string }) {
  try {
    const streamIds = await db
      .select({ id: stream.id })
      .from(stream)
      .where(eq(stream.chatId, chatId))
      .orderBy(asc(stream.createdAt))
      .execute();

    return streamIds.map(({ id }) => id);
  } catch (error) {
    console.error('Failed to get stream ids by chat id from database');
    throw error;
  }
}

export async function getCurrentUserSpace(userId: string) {
  let currentSpace = await getSelectedSpace(userId);
  
  if (!currentSpace) {
    currentSpace = await ensureDefaultSpace(userId);
  }
  
  return currentSpace;
}

/**
 * Invite a user to a space
 */
export async function inviteUserToSpace(spaceId: string, userEmail: string): Promise<{
  success: boolean;
  error?: string;
  space?: any;
  user?: any;
}> {
  try {
    // Get the space
    const space = await getSpaceById(spaceId);
    if (!space) {
      return { success: false, error: 'Space not found' };
    }

    // Get the user to invite
    const [userToInvite] = await getUser(userEmail);
    if (!userToInvite) {
      return { success: false, error: 'User not found' };
    }

    // Check if user is already in the space
    const existingMembership = await db
      .select()
      .from(spaceToUser)
      .where(
        and(
          eq(spaceToUser.spaceId, spaceId),
          eq(spaceToUser.userId, userToInvite.id)
        )
      );

    if (existingMembership.length > 0) {
      return { success: false, error: 'User is already a member of this space' };
    }

    // Add user to space
    await db.insert(spaceToUser).values({
      spaceId,
      userId: userToInvite.id,
    });

    return {
      success: true,
      space,
      user: userToInvite,
    };
  } catch (error) {
    console.error('Error inviting user to space:', error);
    return { success: false, error: 'Failed to invite user to space' };
  }
}

/**
 * Get all members of a space
 */
export async function getSpaceMembers(spaceId: string) {
  try {
    return await db
      .select({
        id: user.id,
        email: user.email,
        name: user.name,
        image: user.image,
        emailVerified: user.emailVerified,
      })
      .from(spaceToUser)
      .innerJoin(user, eq(spaceToUser.userId, user.id))
      .where(eq(spaceToUser.spaceId, spaceId))
      .orderBy(asc(user.email));
  } catch (error) {
    console.error('Error getting space members:', error);
    throw error;
  }
}

export async function updateUserOnboarding(userId: string, hasCompletedOnboarding: boolean) {
  try {
    return await db
      .update(user)
      .set({ hasCompletedOnboarding })
      .where(eq(user.id, userId));
  } catch (error) {
    console.error('Failed to update user onboarding status');
    throw error;
  }
}

export async function updateUserProfileNotes(userId: string, profileNotes: string) {
  try {
    return await db
      .update(user)
      .set({ profileNotes })
      .where(eq(user.id, userId));
  } catch (error) {
    console.error('Failed to update user profile notes');
    throw error;
  }
}

export async function updateUserProfile(userId: string, updates: { name?: string | null; image?: string | null }) {
  try {
    return await db.update(user).set(updates).where(eq(user.id, userId));
  } catch (error) {
    console.error('Failed to update user profile');
    throw error;
  }
}

// Token usage queries

export async function getTokenUsageByMessageId({ messageId }: { messageId: string }) {
  try {
    const [usage] = await db
      .select()
      .from(tokenUsage)
      .where(eq(tokenUsage.messageId, messageId));
    return usage;
  } catch (error) {
    console.error('Failed to get token usage by message id from database');
    throw error;
  }
}

export async function getTokenUsageByChatId({ chatId }: { chatId: string }) {
  try {
    return await db
      .select()
      .from(tokenUsage)
      .where(eq(tokenUsage.chatId, chatId))
      .orderBy(desc(tokenUsage.createdAt));
  } catch (error) {
    console.error('Failed to get token usage by chat id from database');
    throw error;
  }
}

export async function getTokenUsageByUserId({ userId }: { userId: string }) {
  try {
    return await db
      .select({
        id: tokenUsage.id,
        messageId: tokenUsage.messageId,
        chatId: tokenUsage.chatId,
        provider: tokenUsage.provider,
        model: tokenUsage.model,
        promptTokens: tokenUsage.promptTokens,
        completionTokens: tokenUsage.completionTokens,
        totalTokens: tokenUsage.totalTokens,
        inputCost: tokenUsage.inputCost,
        outputCost: tokenUsage.outputCost,
        totalCost: tokenUsage.totalCost,
        providerMetadata: tokenUsage.providerMetadata,
        createdAt: tokenUsage.createdAt,
        chatTitle: chat.title,
      })
      .from(tokenUsage)
      .innerJoin(chat, eq(tokenUsage.chatId, chat.id))
      .where(eq(chat.userId, userId))
      .orderBy(desc(tokenUsage.createdAt));
  } catch (error) {
    console.error('Failed to get token usage by user id from database');
    throw error;
  }
}

export async function getTokenUsageBySpaceId({ spaceId }: { spaceId: string }) {
  try {
    return await db
      .select({
        id: tokenUsage.id,
        messageId: tokenUsage.messageId,
        chatId: tokenUsage.chatId,
        provider: tokenUsage.provider,
        model: tokenUsage.model,
        promptTokens: tokenUsage.promptTokens,
        completionTokens: tokenUsage.completionTokens,
        totalTokens: tokenUsage.totalTokens,
        inputCost: tokenUsage.inputCost,
        outputCost: tokenUsage.outputCost,
        totalCost: tokenUsage.totalCost,
        providerMetadata: tokenUsage.providerMetadata,
        createdAt: tokenUsage.createdAt,
        chatTitle: chat.title,
        userId: chat.userId,
      })
      .from(tokenUsage)
      .innerJoin(chat, eq(tokenUsage.chatId, chat.id))
      .where(eq(chat.spaceId, spaceId))
      .orderBy(desc(tokenUsage.createdAt));
  } catch (error) {
    console.error('Failed to get token usage by space id from database');
    throw error;
  }
}

export async function getTokenUsageSummaryByUserId({ userId }: { userId: string }) {
  try {
    const result = await db
      .select({
        provider: tokenUsage.provider,
        model: tokenUsage.model,
        totalMessages: sql<number>`count(*)`.mapWith(Number),
        totalPromptTokens: sql<number>`sum(${tokenUsage.promptTokens})`.mapWith(Number),
        totalCompletionTokens: sql<number>`sum(${tokenUsage.completionTokens})`.mapWith(Number),
        totalTokens: sql<number>`sum(${tokenUsage.totalTokens})`.mapWith(Number),
        totalCost: sql<number>`sum(${tokenUsage.totalCost})`.mapWith(Number),
      })
      .from(tokenUsage)
      .innerJoin(chat, eq(tokenUsage.chatId, chat.id))
      .where(eq(chat.userId, userId))
      .groupBy(tokenUsage.provider, tokenUsage.model)
      .orderBy(desc(sql`sum(${tokenUsage.totalTokens})`));
    
    return result;
  } catch (error) {
    console.error('Failed to get token usage summary by user id from database');
    throw error;
  }
}
