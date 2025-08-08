import {openai} from '@ai-sdk/openai';
import {customProvider,} from 'ai';
import {createAnthropic} from "@ai-sdk/anthropic";

export const DEFAULT_CHAT_MODEL: string = 'coding-model';

const anthropicBeta = createAnthropic({
    headers: {
      // fine-grained tool streaming opt-in
      'anthropic-beta': 'fine-grained-tool-streaming-2025-05-14',
    },
});

export const myProvider = customProvider({
    languageModels: {
        'chat-model-small': openai('gpt-4.1-mini'),
        'chat-model-large': openai('gpt-4.1'),
        'chat-model-reasoning': openai('o3-mini'),
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
        name: 'Small model',
        description: 'Small model for fast, lightweight tasks',
        provider: 'openai',
        providerDisplayName: 'GPT-4.1 mini',
    },
    {
        id: 'chat-model-large',
        name: 'Large model',
        description: 'Large model for complex, multi-step tasks',
        provider: 'openai',
        providerDisplayName: 'GPT-4.1',
    },
    {
        id: 'coding-model',
        name: 'Coding model',
        description: 'Model for simple tasks with interaction with the codebase',
        provider: 'anthropic',
        providerDisplayName: 'Sonnet 3.7',
    },
    {
        id: 'coding-model-large',
        name: 'Large Coding model',
        description: 'Model for coding tasks, with more complex interactions with the codebase',
        provider: 'anthropic',
        providerDisplayName: 'Sonnet 4',
    },
];
