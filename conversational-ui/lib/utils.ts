import type {
  CoreAssistantMessage,
  CoreToolMessage,
  Message,
  TextStreamPart,
  ToolInvocation,
  ToolSet,
  Attachment,
  UIMessage,
} from 'ai';
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

import type { DBMessage, Document } from '@/lib/db/schema';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface ApplicationError extends Error {
  info: string;
  status: number;
}

export const fetcher = async (url: string) => {
  const res = await fetch(url);

  if (!res.ok) {
    const error = new Error(
      'An error occurred while fetching the data.',
    ) as ApplicationError;

    error.info = await res.json();
    error.status = res.status;

    throw error;
  }

  return res.json();
};

export function getLocalStorage(key: string) {
  if (typeof window !== 'undefined') {
    return JSON.parse(localStorage.getItem(key) || '[]');
  }
  return [];
}

export function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function addToolMessageToChat({
  toolMessage,
  messages,
}: {
  toolMessage: CoreToolMessage;
  messages: Array<Message>;
}): Array<Message> {
  return messages.map((message) => {
    if (message.toolInvocations) {
      return {
        ...message,
        toolInvocations: message.toolInvocations.map((toolInvocation) => {
          const toolResult = toolMessage.content.find(
            (tool) => tool.toolCallId === toolInvocation.toolCallId,
          );

          if (toolResult) {
            return {
              ...toolInvocation,
              state: 'result',
              result: toolResult.result,
            };
          }

          return toolInvocation;
        }),
      };
    }

    return message;
  });
}


export const SUPPORTED_MIME_TYPES = ['image/jpeg', 'image/png', 'application/pdf'] as const;

type ResponseMessageWithoutId = CoreToolMessage | CoreAssistantMessage;
type ResponseMessage = ResponseMessageWithoutId & { 
  id: string;
  experimental_attachments?: Attachment[]; 
};


export function getMostRecentUserMessage(messages: Array<UIMessage>) {
  const userMessages = messages.filter((message) => message.role === 'user');
  return userMessages.at(-1);
}

export function getDocumentTimestampByIndex(
  documents: Array<Document>,
  index: number,
) {
  if (!documents) return new Date();
  if (index > documents.length) return new Date();

  return documents[index].createdAt;
}

export function getInitials(name: string) {
  return name
    .split(' ')
    .map((word) => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

export function generatePastelColor(text: string) {
  if (!text || text === 'Default Space') {
    // Dégradé par défaut plus visible et élégant
    return 'linear-gradient(135deg, #00DC82 0%, #36E4DA 100%)';
  }

  // Génère une couleur basée sur le texte pour les autres cas
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    hash = text.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  const h = hash % 360;
  // Augmentation de la saturation et ajustement de la luminosité pour plus de contraste
  const s = 85 + (hash % 15); // Variation de saturation entre 85-100%
  const l1 = 65 + (hash % 10); // Première couleur
  const l2 = 45 + (hash % 15); // Deuxième couleur plus foncée pour meilleur contraste
  
  return `linear-gradient(135deg, hsl(${h}, ${s}%, ${l1}%) 0%, hsl(${h}, ${s}%, ${l2}%) 100%)`;
}

export function getTrailingMessageId({
  messages,
}: {
  messages: Array<ResponseMessage>;
}): string | null {
  const trailingMessage = messages.at(-1);

  if (!trailingMessage) return null;

  return trailingMessage.id;
}

// Favicon utilities
export const getFallbackFaviconUrls = (url: string) => {
  try {
    const urlObj = new URL(url);
    const domain = urlObj.hostname;
    const protocol = urlObj.protocol;
    const basePath = urlObj.pathname.substring(0, urlObj.pathname.lastIndexOf('/') + 1);
    
    const fallbacks = [];
    
    // If URL has a path, try favicon.ico in that path first
    if (basePath !== '/') {
      fallbacks.push(`${protocol}//${domain}${basePath}favicon.ico`);
    }
    
    // Always try the standard domain root favicon
    fallbacks.push(`${protocol}//${domain}/favicon.ico`);
    
    return fallbacks;
  } catch (e) {
    return [];
  }
};