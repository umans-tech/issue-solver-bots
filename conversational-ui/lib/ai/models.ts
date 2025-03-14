import {openai} from '@ai-sdk/openai';
import {customProvider,} from 'ai';
import {anthropic} from "@ai-sdk/anthropic";

export const DEFAULT_CHAT_MODEL: string = 'chat-model-small';

export const myProvider = customProvider({
    languageModels: {
        'chat-model-small': openai.responses('gpt-4o-mini'),
        'chat-model-large': openai.responses('gpt-4o'),
        'chat-model-reasoning': openai.responses('o3-mini'),
        'coding-model': anthropic('claude-3-7-sonnet-latest'),
        'title-model': openai.responses('gpt-4o-mini'),
        'artifact-model': openai.responses('gpt-4o-mini'),
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
        id: 'coding-model',
        name: 'Coding model',
        description: 'Model for coding tasks',
    },
];
