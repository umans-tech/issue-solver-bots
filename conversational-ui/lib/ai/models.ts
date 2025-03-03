import { openai } from '@ai-sdk/openai';
import { google } from '@ai-sdk/google';
import {
  customProvider,
} from 'ai';

export const DEFAULT_CHAT_MODEL: string = 'chat-model-small';

export const myProvider = customProvider({
  languageModels: {
    'chat-model-small': google('gemini-2.0-flash'),
    'chat-model-large': google('gemini-2.0-pro-exp-02-05'),
    'chat-model-reasoning': google('gemini-2.0-flash-thinking-exp-01-21'),
    'codebase-model': google('gemini-2.0-pro-exp-02-05'),
    'title-model': google('gemini-2.0-flash'),
    'artifact-model': google('gemini-2.0-flash'),
  },
  imageModels: {
    'small-model': openai.image('dall-e-2'),
    'large-model': openai.image('dall-e-3'),
  },
});

interface ChatModel {
  id: string;
  name: string;
  description: string;
}

export const chatModels: Array<ChatModel> = [
  {
    id: 'chat-model-small',
    name: 'Small model',
    description: 'Small model for fast, lightweight tasks',
  },
  {
    id: 'chat-model-large',
    name: 'Large model',
    description: 'Large model for complex, multi-step tasks',
  },
  {
    id: 'chat-model-reasoning',
    name: 'Reasoning model',
    description: 'Uses advanced reasoning',
  },
  {
    id: 'codebase-model',
    name: 'Codebase model',
    description: 'Model with large context ingesting a codebase',
  },
];
