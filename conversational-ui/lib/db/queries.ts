import 'server-only';

import { genSaltSync, hashSync } from 'bcrypt-ts';
import { and, asc, desc, eq, gt, gte, inArray } from 'drizzle-orm';
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';

import {
  user,
  chat,
  type User,
  document,
  type Suggestion,
  suggestion,
  type Message,
  message,
  vote,
  space,
  spaceToUser,
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

export async function createUser(email: string, password: string) {
  const salt = genSaltSync(10);
  const hash = hashSync(password, salt);

  try {
    return await db.insert(user).values({ email, password: hash });
  } catch (error) {
    console.error('Failed to create user in database');
    throw error;
  }
}

export async function saveChat({
  id,
  userId,
  title,
}: {
  id: string;
  userId: string;
  title: string;
}) {
  try {
    return await db.insert(chat).values({
      id,
      createdAt: new Date(),
      userId,
      title,
    });
  } catch (error) {
    console.error('Failed to save chat in database');
    throw error;
  }
}

export async function deleteChatById({ id }: { id: string }) {
  try {
    await db.delete(vote).where(eq(vote.chatId, id));
    await db.delete(message).where(eq(message.chatId, id));

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

export async function getChatById({ id }: { id: string }) {
  try {
    const [selectedChat] = await db.select().from(chat).where(eq(chat.id, id));
    return selectedChat;
  } catch (error) {
    console.error('Failed to get chat by id from database');
    throw error;
  }
}

export async function saveMessages({ messages }: { messages: Partial<Message>[] }) {
  try {
    return await db.insert(message).values(messages as Message[]);
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
  isDefault: boolean = false
) {
  return db
    .insert(space)
    .values({
      name,
      knowledgeBaseId,
      processId,
      isDefault,
      createdAt: new Date(),
      updatedAt: new Date(),
    })
    .returning()
    .then(async (spaces) => {
      if (spaces.length > 0) {
        // Create the space-user relationship
        await db.insert(spaceToUser).values({
          spaceId: spaces[0].id,
          userId: userId,
        });
        return spaces[0];
      }
      return null;
    });
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
    isDefault?: boolean;
  }
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
      true
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
