import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Umans.ai - AI Agents for Software Delivery',
  description: 'Bridge the gap between business needs and technical implementation with AI agents that understand your codebase. Collaborative executable modeling, automated issue resolution, and more.',
  openGraph: {
    title: 'Umans.ai - AI Agents for Software Delivery',
    description: 'Bridge the gap between business needs and technical implementation with AI agents that understand your codebase.',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Umans.ai - AI Agents for Software Delivery',
    description: 'Bridge the gap between business needs and technical implementation with AI agents that understand your codebase.',
  },
};

export default function LandingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
