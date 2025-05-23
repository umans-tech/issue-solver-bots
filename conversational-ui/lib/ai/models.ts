import {openai} from '@ai-sdk/openai';
import {customProvider,} from 'ai';
import {anthropic} from "@ai-sdk/anthropic";

export const DEFAULT_CHAT_MODEL: string = 'coding-model';

export const myProvider = customProvider({
    languageModels: {
        'chat-model-small': openai('gpt-4o-mini'),
        'chat-model-large': openai('gpt-4.1'),
        'chat-model-reasoning': openai('o3-mini'),
        'coding-model-light': anthropic('claude-3-5-sonnet-latest'),
        'coding-model': anthropic('claude-3-7-sonnet-latest'),
        'coding-model-large': anthropic('claude-sonnet-4-20250514'),
        'coding-model-super': anthropic('claude-opus-4-20250514'),
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
        id: 'coding-model-light',
        name: 'Light Coding model',
        description: 'Model for simple tasks with interaction with the codebase',
    },
    {
        id: 'coding-model',
        name: 'Coding model',
        description: 'Model for coding tasks, with more complex interactions with the codebase',
    },
    {
        id: 'coding-model-large',
        name: 'Large Coding model',
        description: 'Model for coding tasks, with more complex interactions with the codebase',
    },
    {
        id: 'coding-model-super',
        name: 'Super Coding model',
        description: 'Model for coding tasks, with more complex interactions with the codebase',
    },
];
