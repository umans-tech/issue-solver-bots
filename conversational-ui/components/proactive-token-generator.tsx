'use client';

import { ExternalLink, Key } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface ProactiveTokenGeneratorProps {
  repositoryUrl: string;
  className?: string;
}

type Provider = 'github' | 'gitlab' | 'azure' | 'unknown';

interface ProviderConfig {
  name: string;
  tokenUrl: string;
  scopes: string[];
  instructions: string;
}

const PROVIDER_CONFIGS: Record<Provider, ProviderConfig> = {
  github: {
    name: 'GitHub',
    tokenUrl: 'https://github.com/settings/tokens/new?description=Umans-AI-Platform&scopes=repo,workflow,read:user',
    scopes: ['repo', 'workflow', 'read:user'],
    instructions: 'Select all listed scopes and generate token'
  },
  gitlab: {
    name: 'GitLab', 
    tokenUrl: 'https://gitlab.com/-/user_settings/personal_access_tokens?name=Umans-AI-Platform&scopes=api,read_user,read_repository,write_repository',
    scopes: ['api', 'read_user', 'read_repository', 'write_repository'],
    instructions: 'Select API, read user, read/write repository scopes'
  },
  azure: {
    name: 'Azure DevOps',
    tokenUrl: 'https://dev.azure.com/',
    scopes: ['Code (read)', 'Code (write)', 'Project and team (read)'],
    instructions: 'Go to User Settings > Personal Access Tokens'
  },
  unknown: {
    name: 'Repository',
    tokenUrl: '',
    scopes: [],
    instructions: 'Configure access token in your repository settings'
  }
};

function detectProvider(url: string): Provider {
  const lowercaseUrl = url.toLowerCase();
  
  if (lowercaseUrl.includes('github.com')) return 'github';
  if (lowercaseUrl.includes('gitlab.com') || lowercaseUrl.includes('gitlab.')) return 'gitlab';
  if (lowercaseUrl.includes('dev.azure.com') || lowercaseUrl.includes('visualstudio.com')) return 'azure';
  
  return 'unknown';
}

export function ProactiveTokenGenerator({ repositoryUrl, className = '' }: ProactiveTokenGeneratorProps) {
  if (!repositoryUrl.trim()) {
    return null;
  }

  const provider = detectProvider(repositoryUrl);
  const config = PROVIDER_CONFIGS[provider];

  if (provider === 'unknown') {
    return (
      <div className={`text-xs text-muted-foreground ${className}`}>
        <div className="flex items-center gap-1">
          <Key className="h-3 w-3" />
          <span>Configure access token in your repository settings</span>
        </div>
      </div>
    );
  }

  const handleGenerateToken = () => {
    if (config.tokenUrl) {
      window.open(config.tokenUrl, '_blank');
    }
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <Key className="h-3 w-3" />
          <span>Need a token for {config.name}?</span>
        </div>
        
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="h-6 text-xs"
          onClick={handleGenerateToken}
        >
          <ExternalLink className="h-3 w-3 mr-1" />
          Generate Token
        </Button>
      </div>
      
      <div className="text-xs text-muted-foreground">
        <div className="mb-1">Required scopes:</div>
        <div className="flex flex-wrap gap-1">
          {config.scopes.map(scope => (
            <Badge key={scope} variant="outline" className="text-xs h-4">
              {scope}
            </Badge>
          ))}
        </div>
      </div>
    </div>
  );
} 