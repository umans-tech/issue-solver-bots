import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Umans.ai - AI coding agents and chat with your codebase',
  description: 'Umans connects to your repo so you can chat with large codebases, delegate coding tasks to secure AI agents that ship PRs, and generate living docs grounded in your code.',
  openGraph: {
    title: 'Umans.ai - AI coding agents and chat with your codebase',
    description: 'Umans connects to your repo so you can chat with large codebases, delegate coding tasks to secure AI agents that ship PRs, and generate living docs grounded in your code.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Umans.ai - AI coding agents and chat with your codebase',
    description: 'Umans connects to your repo so you can chat with large codebases, delegate coding tasks to secure AI agents that ship PRs, and generate living docs grounded in your code.',
  },
};

export default function LandingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}