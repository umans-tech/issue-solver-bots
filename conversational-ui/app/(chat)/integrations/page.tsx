'use client';

import { useState } from 'react';
import { GitHubLogoIcon } from '@radix-ui/react-icons';
import { SiGitlab, SiNotion, SiLinear, SiPostgresql, SiGit, SiFigma, SiSlack } from 'react-icons/si';
import { VscAzureDevops } from 'react-icons/vsc';
import { Clock } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { IntegrationsHeader } from '@/components/integrations-header';
import { RepoConnectionDialog } from '@/components/repo-connection-dialog';
import { NotionIntegrationDialog } from '@/components/notion-integration-dialog';

interface Integration {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  category:
    | 'Code Repository'
    | 'Knowledge Base'
    | 'Project Management'
    | 'Communication'
    | 'Design'
    | 'Database';
  status: 'available' | 'coming-soon';
}

const integrations: Integration[] = [
  {
    id: 'github',
    name: 'GitHub',
    description: 'Connect your GitHub repositories to analyze code, create issues, and manage pull requests.',
    icon: GitHubLogoIcon,
    category: 'Code Repository',
    status: 'available'
  },
  {
    id: 'gitlab',
    name: 'GitLab',
    description: 'Integrate with GitLab for comprehensive DevOps workflow management.',
    icon: ({ className }) => <SiGitlab className={className} color="default" />,
    category: 'Code Repository',
    status: 'available'
  },
  {
    id: 'azure-devops',
    name: 'Azure DevOps',
    description: 'Connect to Azure DevOps for enterprise-grade development lifecycle management.',
    icon: VscAzureDevops,
    category: 'Code Repository',
    status: 'available'
  },
  {
    id: 'self-hosted-git',
    name: 'Self-hosted Git',
    description: 'Connect to your private Git repositories with custom endpoints.',
    icon: ({ className }) => <SiGit className={className} color="default" />,
    category: 'Code Repository',
    status: 'available'
  },
  {
    id: 'notion',
    name: 'Notion',
    description: 'Integrate with Notion to access and manage your knowledge base and documentation.',
    icon: ({ className }) => <SiNotion className={className} color="default" />,
    category: 'Knowledge Base',
    status: 'available'
  },
  {
    id: 'linear',
    name: 'Linear',
    description: 'Connect Linear to streamline issue tracking and project management workflows.',
    icon: ({ className }) => <SiLinear className={className} color="default" />,
    category: 'Project Management',
    status: 'coming-soon'
  },
  {
    id: 'postgresql',
    name: 'PostgreSQL',
    description: 'Direct database integration for querying and analyzing your PostgreSQL data.',
    icon: ({ className }) => <SiPostgresql className={className} color="default" />,
    category: 'Database',
    status: 'coming-soon'
  },
  {
    id: 'slack',
    name: 'Slack',
    description: 'Bring conversations into Umans by syncing channels, threads, and notifications.',
    icon: ({ className }) => <SiSlack className={className} color="default" />,
    category: 'Communication',
    status: 'coming-soon'
  },
  {
    id: 'figma',
    name: 'Figma',
    description: 'Review and reference your design files directly inside Umans.',
    icon: ({ className }) => <SiFigma className={className} color="default" />,
    category: 'Design',
    status: 'coming-soon'
  }
];

const categoryOrder: Record<Integration['category'], number> = {
  'Knowledge Base': 0,
  'Code Repository': 1,
  'Project Management': 2,
  'Communication': 3,
  'Design': 4,
  'Database': 5
};

const sortedIntegrations = [...integrations].sort((a, b) => {
  const categoryDifference = categoryOrder[a.category] - categoryOrder[b.category];

  if (categoryDifference !== 0) {
    return categoryDifference;
  }

  if (a.status !== b.status) {
    return a.status === 'available' ? -1 : 1;
  }

  return a.name.localeCompare(b.name);
});

export default function IntegrationsPage() {
  const [showRepoDialog, setShowRepoDialog] = useState(false);
  const [showNotionDialog, setShowNotionDialog] = useState(false);

  const handleConnect = (integrationId: string) => {
    switch (integrationId) {
      case 'github':
      case 'gitlab':
      case 'azure-devops':
      case 'self-hosted-git':
        setShowRepoDialog(true);
        break;
      case 'notion':
        setShowNotionDialog(true);
        break;
      default:
        console.log('Connecting to integration:', integrationId);
    }
  };

  return (
    <>
      <div className="flex flex-col min-w-0 h-dvh bg-background">
        <IntegrationsHeader />

        <div className="flex-1 overflow-auto">
          <div className="container mx-auto p-6 space-y-8">
            <div className="space-y-2">
              <h1 className="text-3xl font-bold tracking-tight">Integrations</h1>
              <p className="text-muted-foreground">
                Connect your tools and services to enhance your workflow and productivity.
              </p>
            </div>

            <section>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
                {sortedIntegrations.map((integration) => {
                  const IconComponent = integration.icon;
                  const isAvailable = integration.status === 'available';

                  return (
                    <button
                      key={integration.id}
                      type="button"
                      onClick={isAvailable ? () => handleConnect(integration.id) : undefined}
                      disabled={!isAvailable}
                      className="group relative flex w-full min-w-[260px] flex-col gap-3 rounded-2xl border border-border/60 bg-card/70 px-4 py-4 text-left transition-all duration-200 hover:z-20 hover:-translate-y-1 hover:scale-[1.02] hover:border-primary/40 hover:bg-background/95 hover:shadow-xl focus-visible:z-20 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:border-dashed disabled:opacity-80"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="flex items-center gap-3">
                          <span className="grid h-9 w-9 place-items-center rounded-xl bg-muted/70 text-foreground transition-colors duration-200 group-hover:bg-primary/10 group-focus:bg-primary/10">
                            <IconComponent className="h-5 w-5" />
                          </span>
                          <span className="flex flex-col">
                            <span className="font-semibold leading-tight whitespace-nowrap">{integration.name}</span>
                            <span className="text-xs text-muted-foreground">{integration.category}</span>
                          </span>
                        </span>

                        {isAvailable ? (
                          <span className="inline-flex items-center text-sm font-medium text-primary">
                            Connect
                          </span>
                        ) : (
                          <Badge
                            variant="outline"
                            className="flex items-center gap-1 text-[11px] uppercase tracking-wide text-muted-foreground"
                          >
                            <Clock className="h-3 w-3" />
                            Soon
                          </Badge>
                        )}
                      </div>

                    </button>
                  );
                })}
              </div>
            </section>
          </div>
        </div>
      </div>

      <RepoConnectionDialog 
        key={/* key by space if available via a sessioned header; keep stable here */ 'integrations'} 
        open={showRepoDialog} 
        onOpenChange={setShowRepoDialog} 
      />
      <NotionIntegrationDialog 
        open={showNotionDialog} 
        onOpenChange={setShowNotionDialog} 
      />
    </>
  );
}
