import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Umans – AI coding agents for teams that ship on complex systems',
  description: 'Umans is an AI coding agent platform that helps software teams understand large codebases faster, offload repetitive fixes to remote agents that open PRs, and keep docs and architecture diagrams in sync with the code, with a self hosted model option for enterprises.',
};

export default function LandingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
