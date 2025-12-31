import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'envs by Umans | Repo-ready sandboxes for AI agents',
  description: 'Give your AI agents a real developer environment. Deterministic, MCP-native sandboxes that spin up in seconds. Snapshot state, fork instantly, and stream output.',
  openGraph: {
    title: 'envs by Umans | Repo-ready sandboxes for AI agents',
    description: 'Give your AI agents a real developer environment. Deterministic, MCP-native sandboxes that spin up in seconds.',
    url: 'https://umans.ai/offers/envs',
    siteName: 'Umans AI',
    locale: 'en_US',
    type: 'website',
    images: [
      {
        url: 'https://umans.ai/og-envs.png', 
        width: 1200,
        height: 630,
        alt: 'envs by Umans - Sandboxes for AI Agents',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'envs by Umans | Repo-ready sandboxes for AI agents',
    description: 'Give your AI agents a real developer environment. Deterministic, MCP-native sandboxes that spin up in seconds.',
    creator: '@umans_ai',
    images: ['https://umans.ai/og-envs.png'],
  },
  alternates: {
    canonical: '/offers/envs',
  },
  keywords: ['AI agents', 'sandboxes', 'MCP', 'developer tools', 'coding agents', 'reproducibility', 'E2E testing'],
};

export default function EnvsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
