
<img alt="umans.ai frontend" src="public/umans-u-logo.svg" width="40" align="left"/>
<img alt="umans.ai platform" src="public/umans-logo.svg" width="50" align="right"/>
<a href="https://umans.ai/">
  <h1 align="center">umans.ai User Interface</h1>
</a>

<p align="center">
  The user interface for umans.ai, a multi-AI agent platform designed to help software development teams master complexity and deliver value continuously.
</p>

<p align="center">
  <a href="#tech-stack"><strong>Tech Stack</strong></a> ·
  <a href="#running-locally"><strong>Running Locally</strong></a> ·
  <a href="#authors"><strong>Authors</strong></a>
</p>

<br/>

## Tech Stack

- **Next.js**: Framework for building the frontend with React.
- **Vercel AI SDK**: Facilitates AI interactions and streaming chat UI.
- **Supabase**: Provides authentication and database services.
- **Tailwind CSS**: Utility-first CSS framework for styling.
- **Radix UI**: Headless component primitives for building accessible UI.
- **Phosphor Icons**: Icon set for UI components.
- **shadcn/ui**: Pre-built UI components for rapid development.

### Set up GitHub OAuth

This demo uses GitHub OAuth. Follow the [GitHub OAuth setup steps](https://supabase.com/docs/guides/auth/social-login/auth-github) on your Supabase project.

### Configure your site URL

In the Supabase Dashboard, navigate to [Auth > URL configuration](https://app.supabase.com/project/_/auth/url-configuration) and set your Vercel URL as the site URL.

## Running Locally

You will need to use the environment variables [defined in `.env.example`](.env.example) to run the umans.ai frontend. It's recommended you use [Vercel Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables) for this, but a `.env` file is all that is necessary.

> Note: You should not commit your `.env` file or it will expose secrets that will allow others to control access to your various OpenAI and authentication provider accounts.

Copy the `.env.example` file and populate the required env vars:

```bash
cp .env.example .env
```

[Install the Supabase CLI](https://supabase.com/docs/guides/cli) and start the local Supabase stack:

```bash
npm install supabase --save-dev
npx supabase start
```

Install the local dependencies and start dev mode:

```bash
pnpm install
pnpm dev
```

Your app should now be running on [localhost:3000](http://localhost:3000/).

## Authors

This project is created by the umans.ai team, with contributions from:

- [Wassel Alazhar](https://github.com/jcraftsman) - [Systems Explorer](https://umans.tech/authors/wassel-alazhar/)
- [Naji Alazhar](https://github.com/alazharn) - [Systems Deep Diver](https://umans.tech/authors/naji-alazhar/)

## Credits

This project is built upon the open-source template [Next.js AI Chatbot](https://github.com/supabase-community/vercel-ai-chatbot), created by the following contributors:

- **Jared Palmer** ([@jaredpalmer](https://twitter.com/jaredpalmer)) - [Vercel](https://vercel.com)
- **Shu Ding** ([@shuding\_](https://twitter.com/shuding_)) - [Vercel](https://vercel.com)
- **shadcn** ([@shadcn](https://twitter.com/shadcn)) - [Contractor](https://shadcn.com)
- **Thor Schaeff** ([@thorwebdev](https://twitter.com/thorwebdev)) - [Supabaseifier](https://thor.bio)

We appreciate their work and contributions to the open-source community, which have made this project possible.
