import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Umans – AI coding agents for teams that ship on complex systems',
  description: 'Umans is an AI coding agent platform that helps software teams understand large codebases faster, offload repetitive fixes to remote agents that open PRs, and keep docs and architecture diagrams in sync with the code, with a self hosted model option for enterprises.',
  openGraph: {
    title: 'Umans – AI coding agents for teams that ship on complex systems',
    description: 'Umans is an AI coding agent platform that helps software teams understand large codebases faster, offload repetitive fixes to remote agents that open PRs, and keep docs and architecture diagrams in sync with the code.',
    url: 'https://umans.ai',
    siteName: 'Umans AI',
    images: [
      {
        url: 'https://umans.ai/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Umans AI Platform',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Umans – AI coding agents for teams that ship on complex systems',
    description: 'Umans is an AI coding agent platform that helps software teams understand large codebases faster, offload repetitive fixes to remote agents that open PRs, and keep docs and architecture diagrams in sync with the code.',
    images: ['https://umans.ai/og-image.png'],
    creator: '@umans_ai',
  },
};

export default function LandingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}