<img alt="umans.ai frontend" src="public/images/umans-u-logo.svg" height="40" align="left"/>
<img alt="umans.ai platform" src="public/images/umans-logo.svg" height="40" align="right"/>
<a href="https://umans.ai/">
  <h1 align="center">umans.ai User Interface</h1>
</a>

<p align="center">
  <a href="#features"><strong>Tech Stack</strong></a> ·
  <a href="#model-providers"><strong>Model Providers</strong></a> ·
  <a href="#running-locally"><strong>Running locally</strong></a>
</p>
<br/>

## Tech Stack

- [Next.js](https://nextjs.org) App Router
  - Advanced routing for seamless navigation and performance
  - React Server Components (RSCs) and Server Actions for server-side rendering and increased performance
- [AI SDK](https://sdk.vercel.ai/docs)
  - Unified API for generating text, structured objects, and tool calls with LLMs
  - Hooks for building dynamic chat and generative user interfaces
  - Supports OpenAI (default), Anthropic, Cohere, and other model providers
- [shadcn/ui](https://ui.shadcn.com)
  - Styling with [Tailwind CSS](https://tailwindcss.com)
  - Component primitives from [Radix UI](https://radix-ui.com) for accessibility and flexibility
- Data Persistence
  - Postgresql for saving chat history and user data
  - [Vercel Blob](https://vercel.com/storage/blob) for efficient file storage
  - Redis for caching, rate limiting, and session management
- [NextAuth.js](https://github.com/nextauthjs/next-auth)
  - Simple and secure authentication

## Model Providers

This template ships with OpenAI `gpt-4o` as the default. However, with the [AI SDK](https://sdk.vercel.ai/docs), you can switch LLM providers to [OpenAI](https://openai.com), [Anthropic](https://anthropic.com), [Cohere](https://cohere.com/), and [many more](https://sdk.vercel.ai/providers/ai-sdk-providers) with just a few lines of code.

## Running locally

You will need to use the environment variables [defined in `.env.example`](.env.example) to run Next.js conversationa UI. 

> Note: You should not commit your `.env` file or it will expose secrets that will allow others to control access to your various OpenAI and authentication provider accounts.


```bash
pnpm install
pnpm dev
```

Your app should now be running locally on [localhost:3000](http://localhost:3000/).
