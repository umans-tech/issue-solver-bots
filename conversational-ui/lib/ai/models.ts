import {openai, createOpenAI} from '@ai-sdk/openai';
import {customProvider,} from 'ai';
import {createAnthropic} from "@ai-sdk/anthropic";

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
        'chat-model-small': openaiProvider.responses('gpt-5-mini'),
        'chat-model-large': openaiProvider.responses('gpt-5'),
        'coding-model-light': anthropicBeta('claude-3-5-sonnet-latest'),
        'coding-model': anthropicBeta('claude-3-7-sonnet-latest'),
        'coding-model-large': anthropicBeta('claude-sonnet-4-20250514'),
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
    provider: 'openai' | 'anthropic';
    providerDisplayName: string;
}

export const chatModels: Array<ChatModel> = [
    {
        id: 'chat-model-small',
        name: 'Quick Analysis',
        description: 'Fast analysis for quick insights and lightweight tasks',
        provider: 'openai',
        providerDisplayName: 'GPT-5 mini',
    },
    {
        id: 'chat-model-large',
        name: 'Analysis',
        description: 'Deep analysis for complex, multi-step business problems',
        provider: 'openai',
        providerDisplayName: 'GPT-5',
    },
    {
        id: 'coding-model',
        name: 'Engineering Light',
        description: 'Quick engineering tasks and code assistance',
        provider: 'anthropic',
        providerDisplayName: 'Sonnet 3.7',
    },
    {
        id: 'coding-model-large',
        name: 'Engineering',
        description: 'Advanced engineering for complex technical projects',
        provider: 'anthropic',
        providerDisplayName: 'Sonnet 4',
    },
];
