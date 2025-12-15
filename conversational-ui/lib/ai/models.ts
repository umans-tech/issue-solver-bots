import { createOpenAI, openai } from '@ai-sdk/openai';
import { customProvider } from 'ai';
import { createAnthropic } from '@ai-sdk/anthropic';
import { google } from '@ai-sdk/google';

export const DEFAULT_CHAT_MODEL: string = 'coding-model';

const openaiProvider = createOpenAI();

const anthropicBeta = createAnthropic({
  headers: {
    // fine-grained tool streaming opt-in
    'anthropic-beta': 'fine-grained-tool-streaming-2025-05-14',
  },
});

export const myProvider = customProvider({
  languageModels: {
    'chat-model-small-codex': openaiProvider.responses('gpt-5.1-codex-mini'),
    'chat-model-large': openaiProvider.responses('gpt-5.2'),
    'chat-model-large-codex': openaiProvider.responses('gpt-5.1-codex'),
    'chat-model-gemini': google('gemini-3-pro-preview'),
    'coding-model-light': anthropicBeta('claude-haiku-4-5-20251001'),
    'coding-model': anthropicBeta('claude-sonnet-4-20250514'),
    'coding-model-large': anthropicBeta('claude-sonnet-4-5-20250929'),
    'coding-model-super': anthropicBeta('claude-opus-4-20250514'),
    'title-model': openai('gpt-4o-mini'),
    'artifact-model': openai('gpt-4o'),
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
  provider: 'openai' | 'anthropic' | 'google';
  providerDisplayName: string;
}

export const chatModels: Array<ChatModel> = [
  {
    id: 'chat-model-small-codex',
    name: 'Quick Code Analysis',
    description:
      'Fast analysis for quick insights and lightweight coding tasks',
    provider: 'openai',
    providerDisplayName: 'GPT-5.1 codex mini',
  },
  {
    id: 'chat-model-large',
    name: 'Analysis',
    description: 'Deep analysis for complex, multi-step business problems',
    provider: 'openai',
    providerDisplayName: 'GPT-5.2',
  },
  {
    id: 'chat-model-large-codex',
    name: 'Coding',
    description: 'Deep analysis for complex, multi-step coding problems',
    provider: 'openai',
    providerDisplayName: 'GPT-5.1 codex',
  },
  {
    id: 'coding-model-light',
    name: 'Engineering Light',
    description: 'Quick engineering tasks and code assistance',
    provider: 'anthropic',
    providerDisplayName: 'Haiku 4.5',
  },
  {
    id: 'coding-model-large',
    name: 'Engineering',
    description: 'Advanced engineering for complex technical projects',
    provider: 'anthropic',
    providerDisplayName: 'Sonnet 4.5',
  },
  {
    id: 'chat-model-gemini',
    name: 'Advanced Analysis',
    description: 'Advanced analysis for complex technical projects',
    provider: 'google',
    providerDisplayName: 'Gemini 3 Pro Preview',
  },
];
