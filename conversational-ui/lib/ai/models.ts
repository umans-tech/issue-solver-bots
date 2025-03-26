import {openai} from '@ai-sdk/openai';
import {customProvider,} from 'ai';
import {anthropic} from "@ai-sdk/anthropic";
import {deepseek} from '@ai-sdk/deepseek';

export const DEFAULT_CHAT_MODEL: string = 'chat-model-small';

export const myProvider = customProvider({
    languageModels: {
        'chat-model-small': openai('gpt-4o-mini'),
        'chat-model-large': openai('gpt-4o'),
        'chat-model-reasoning': openai('o3-mini'),
        'coding-model-light': deepseek('deepseek-chat'),
        'coding-model': anthropic('claude-3-7-sonnet-latest'),
        'title-model': openai('gpt-4o-mini'),
        'artifact-model': openai('gpt-4o-mini'),
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
];
