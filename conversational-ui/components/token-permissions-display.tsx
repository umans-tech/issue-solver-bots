'use client';

import { AlertCircle, CheckCircle, ExternalLink, ChevronDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useState } from 'react';

interface GitHubTokenPermissions {
  scopes: string[];
  has_repo: boolean;
  has_workflow: boolean;
  has_read_user: boolean;
  missing_scopes: string[];
  is_optimal: boolean;
}

interface TokenPermissionsDisplayProps {
  permissions: GitHubTokenPermissions | null;
  repositoryUrl?: string;
}

const SCOPE_INFO = {
  repo: {
    name: 'Repository Access',
    description: 'Full access to repositories, issues, and pull requests'
  },
  workflow: {
    name: 'GitHub Actions',
    description: 'Access to GitHub Actions workflows'
  },
  'read:user': {
    name: 'User Profile', 
    description: 'Read user profile information'
  }
};

export function TokenPermissionsDisplay({ permissions, repositoryUrl }: TokenPermissionsDisplayProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!permissions) {
    return null;
  }

  const generateTokenUrl = () => {
    const baseUrl = 'https://github.com/settings/tokens/new';
    const params = new URLSearchParams({
      description: 'Umans-AI-Platform',
      scopes: 'repo,workflow,read:user'
    });
    return `${baseUrl}?${params.toString()}`;
  };

  const isGitHubRepo = repositoryUrl && repositoryUrl.toLowerCase().includes('github.com');

  if (!isGitHubRepo) {
    return (
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <CheckCircle className="h-4 w-4 text-green-500" />
            Repository Connected
          </CardTitle>
        </CardHeader>
      </Card>
    );
  }

  const requiredScopes = ['repo', 'workflow', 'read:user'];
  const totalRequired = requiredScopes.length;
  const hasCount = requiredScopes.filter(scope => {
    if (scope === 'read:user') return permissions.has_read_user;
    if (scope === 'repo') return permissions.has_repo;
    if (scope === 'workflow') return permissions.has_workflow;
    return false;
  }).length;

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {permissions.is_optimal ? (
              <CheckCircle className="h-4 w-4 text-green-500" />
            ) : (
              <AlertCircle className="h-4 w-4 text-amber-500" />
            )}
            <CardTitle className="text-sm">Token Permissions</CardTitle>
            <Badge variant={permissions.is_optimal ? "default" : "secondary"}>
              {hasCount}/{totalRequired}
            </Badge>
          </div>
          
          <Button 
            variant="ghost" 
            size="sm" 
            className="h-6 w-6 p-0"
            onClick={() => setIsExpanded(!isExpanded)}
          >
            <ChevronDown className={`h-3 w-3 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
          </Button>
        </div>
        
        {!permissions.is_optimal && (
          <CardDescription className="text-xs">
            Missing {permissions.missing_scopes.length} permission{permissions.missing_scopes.length !== 1 ? 's' : ''}
          </CardDescription>
        )}
      </CardHeader>

      {isExpanded && (
        <CardContent className="pt-0 space-y-3">
          {/* Permission Details */}
          <div className="grid gap-2">
            {Object.entries(SCOPE_INFO).map(([scope, info]) => {
              const hasPermission = permissions.scopes.includes(scope) || 
                (scope === 'read:user' && permissions.has_read_user);
              
              return (
                <div key={scope} className="flex items-center gap-2 text-xs">
                  {hasPermission ? (
                    <CheckCircle className="h-3 w-3 text-green-500 flex-shrink-0" />
                  ) : (
                    <AlertCircle className="h-3 w-3 text-red-500 flex-shrink-0" />
                  )}
                  <span className="font-medium">{info.name}</span>
                  <Badge variant="outline" className="text-xs h-4">
                    {scope}
                  </Badge>
                </div>
              );
            })}
          </div>

          {/* Generate Token Button */}
          {!permissions.is_optimal && (
            <div className="pt-2 border-t">
              <Button
                variant="outline"
                size="sm"
                className="w-full h-7 text-xs"
                onClick={() => window.open(generateTokenUrl(), '_blank')}
              >
                <ExternalLink className="h-3 w-3 mr-1" />
                Generate Optimal Token
              </Button>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
} 