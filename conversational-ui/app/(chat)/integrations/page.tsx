'use client';

import { useState } from 'react';
import { GitHubLogoIcon } from '@radix-ui/react-icons';
import { SiGitlab, SiNotion, SiLinear, SiPostgresql, SiGit } from 'react-icons/si';
import { VscAzureDevops } from 'react-icons/vsc';
import { Database, FileText, CheckCircle2, Clock, ExternalLink, GitBranch } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { IntegrationsHeader } from '@/components/integrations-header';
import { RepoConnectionDialog } from '@/components/repo-connection-dialog';

interface Integration {
  id: string;
  name: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  category: 'Code Repository' | 'Knowledge Base' | 'Database';
  status: 'available' | 'coming-soon';
  features: string[];
}

const integrations: Integration[] = [
  {
    id: 'github',
    name: 'GitHub',
    description: 'Connect your GitHub repositories to analyze code, create issues, and manage pull requests.',
    icon: GitHubLogoIcon,
    category: 'Code Repository',
    status: 'available',
    features: ['Code analysis', 'Issue management', 'PR automation', 'Repository insights']
  },
  {
    id: 'gitlab',
    name: 'GitLab',
    description: 'Integrate with GitLab for comprehensive DevOps workflow management.',
    icon: ({ className }) => <SiGitlab className={className} color="default" />,
    category: 'Code Repository',
    status: 'available',
    features: ['CI/CD integration', 'Merge requests', 'Issue tracking', 'Code review']
  },
  {
    id: 'azure-devops',
    name: 'Azure DevOps',
    description: 'Connect to Azure DevOps for enterprise-grade development lifecycle management.',
    icon: VscAzureDevops,
    category: 'Code Repository',
    status: 'available',
    features: ['Work items', 'Pipelines', 'Repositories', 'Test plans']
  },
  {
    id: 'self-hosted-git',
    name: 'Self-hosted Git',
    description: 'Connect to your private Git repositories with custom endpoints.',
    icon: ({ className }) => <SiGit className={className} color="default" />,
    category: 'Code Repository',
    status: 'available',
    features: ['Custom endpoints', 'SSH/HTTPS', 'Private repos', 'Webhooks']
  },
  {
    id: 'notion',
    name: 'Notion',
    description: 'Integrate with Notion to access and manage your knowledge base and documentation.',
    icon: ({ className }) => <SiNotion className={className} color="default" />,
    category: 'Knowledge Base',
    status: 'coming-soon',
    features: ['Page sync', 'Database queries', 'Content search', 'Real-time updates']
  },
  {
    id: 'linear',
    name: 'Linear',
    description: 'Connect Linear to streamline issue tracking and project management workflows.',
    icon: ({ className }) => <SiLinear className={className} color="default" />,
    category: 'Knowledge Base',
    status: 'coming-soon',
    features: ['Issue sync', 'Project tracking', 'Team workflows', 'Status updates']
  },
  {
    id: 'postgresql',
    name: 'PostgreSQL',
    description: 'Direct database integration for querying and analyzing your PostgreSQL data.',
    icon: ({ className }) => <SiPostgresql className={className} color="default" />,
    category: 'Database',
    status: 'coming-soon',
    features: ['Query execution', 'Schema analysis', 'Data visualization', 'Performance insights']
  }
];

export default function IntegrationsPage() {
  const [showRepoDialog, setShowRepoDialog] = useState(false);
  const availableIntegrations = integrations.filter(integration => integration.status === 'available');
  const comingSoonIntegrations = integrations.filter(integration => integration.status === 'coming-soon');

  const handleConnect = (integrationId: string) => {
    // For code repository integrations, open the repo connection dialog
    const integration = integrations.find(i => i.id === integrationId);
    if (integration && integration.category === 'Code Repository') {
      setShowRepoDialog(true);
    } else {
      // TODO: Implement other integration types
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

            {/* Available Integrations */}
            <section className="space-y-4">
              <div className="flex items-center gap-2">
                <h2 className="text-2xl font-semibold">Available Now</h2>
                <Badge variant="default" className="bg-green-100 text-green-800 border-green-200">
                  <CheckCircle2 className="w-3 h-3 mr-1" />
                  Ready
                </Badge>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {availableIntegrations.map((integration) => {
                  const IconComponent = integration.icon;
                  return (
                    <Card key={integration.id} className="hover:shadow-lg transition-shadow">
                      <CardHeader className="pb-4">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-muted rounded-lg">
                              <IconComponent className="w-6 h-6" />
                            </div>
                            <div>
                              <CardTitle className="text-lg">{integration.name}</CardTitle>
                              <Badge variant="outline" className="mt-1 text-xs">
                                {integration.category}
                              </Badge>
                            </div>
                          </div>
                        </div>
                        <CardDescription className="mt-3">
                          {integration.description}
                        </CardDescription>
                      </CardHeader>
                      
                      <CardContent className="pt-0">
                        <div className="space-y-4">
                          <div>
                            <h4 className="text-sm font-medium mb-2">Features</h4>
                            <div className="flex flex-wrap gap-2">
                              {integration.features.map((feature) => (
                                <Badge key={feature} variant="secondary" className="text-xs">
                                  {feature}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          
                          <Button 
                            onClick={() => handleConnect(integration.id)}
                            className="w-full"
                          >
                            Connect
                            <ExternalLink className="w-4 h-4 ml-2" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </section>

            {/* Coming Soon Integrations */}
            <section className="space-y-4">
              <div className="flex items-center gap-2">
                <h2 className="text-2xl font-semibold">Coming Soon</h2>
                <Badge variant="secondary" className="bg-blue-100 text-blue-800 border-blue-200">
                  <Clock className="w-3 h-3 mr-1" />
                  In Development
                </Badge>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {comingSoonIntegrations.map((integration) => {
                  const IconComponent = integration.icon;
                  return (
                    <Card key={integration.id} className="opacity-75 border-dashed">
                      <CardHeader className="pb-4">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-muted rounded-lg opacity-50">
                              <IconComponent className="w-6 h-6" />
                            </div>
                            <div>
                              <CardTitle className="text-lg text-muted-foreground">
                                {integration.name}
                              </CardTitle>
                              <Badge variant="outline" className="mt-1 text-xs">
                                {integration.category}
                              </Badge>
                            </div>
                          </div>
                        </div>
                        <CardDescription className="mt-3">
                          {integration.description}
                        </CardDescription>
                      </CardHeader>
                      
                      <CardContent className="pt-0">
                        <div className="space-y-4">
                          <div>
                            <h4 className="text-sm font-medium mb-2 text-muted-foreground">
                              Planned Features
                            </h4>
                            <div className="flex flex-wrap gap-2">
                              {integration.features.map((feature) => (
                                <Badge key={feature} variant="outline" className="text-xs opacity-60">
                                  {feature}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          
                          <Button 
                            disabled
                            variant="secondary"
                            className="w-full"
                          >
                            Coming Soon
                            <Clock className="w-4 h-4 ml-2" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </section>
          </div>
        </div>
      </div>

      <RepoConnectionDialog 
        open={showRepoDialog} 
        onOpenChange={setShowRepoDialog} 
      />
    </>
  );
} 