'use client';

import { AlertCircle, CheckCircle, Copy, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { toast } from 'sonner';

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
    description: 'Full access to repositories, issues, and pull requests',
    features: ['Read/write repository files', 'Create and manage issues', 'Create and manage pull requests', 'Search code']
  },
  workflow: {
    name: 'GitHub Actions',
    description: 'Access to GitHub Actions workflows',
    features: ['View workflow runs', 'Access workflow logs', 'Monitor CI/CD status']
  },
  'read:user': {
    name: 'User Profile',
    description: 'Read user profile information',
    features: ['Display profile information', 'Authentication validation']
  }
};

export function TokenPermissionsDisplay({ permissions, repositoryUrl }: TokenPermissionsDisplayProps) {
  if (!permissions) {
    return null;
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

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
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <CheckCircle className="h-5 w-5 text-green-500" />
            Repository Connected
          </CardTitle>
          <CardDescription>
            Token permissions analysis is available for GitHub repositories only.
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {permissions.is_optimal ? (
              <CheckCircle className="h-5 w-5 text-green-500" />
            ) : (
              <AlertCircle className="h-5 w-5 text-amber-500" />
            )}
            Token Permissions
          </CardTitle>
          <CardDescription>
            Your GitHub token permissions and feature availability
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Permission Status Grid */}
          <div className="grid gap-3">
            {Object.entries(SCOPE_INFO).map(([scope, info]) => {
              const hasPermission = permissions.scopes.includes(scope) || 
                (scope === 'read:user' && permissions.has_read_user);
              
              return (
                <div key={scope} className="flex items-start gap-3 p-3 border rounded-lg">
                  {hasPermission ? (
                    <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-500 mt-0.5 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium">{info.name}</span>
                      <Badge variant={hasPermission ? "default" : "destructive"} className="text-xs">
                        {scope}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mb-2">{info.description}</p>
                    <div className="text-xs text-muted-foreground">
                      <span className="font-medium">Enables:</span> {info.features.join(', ')}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Raw Scopes Display */}
          <div className="border-t pt-4">
            <h4 className="text-sm font-medium mb-2">Current Token Scopes</h4>
            <div className="flex flex-wrap gap-1">
              {permissions.scopes.length > 0 ? (
                permissions.scopes.map((scope) => (
                  <Badge key={scope} variant="outline" className="text-xs">
                    {scope}
                  </Badge>
                ))
              ) : (
                <span className="text-sm text-muted-foreground">No scopes detected</span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Missing Permissions Alert */}
      {!permissions.is_optimal && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Missing Permissions</AlertTitle>
          <AlertDescription className="mt-2">
            <div className="space-y-2">
              <p>
                Your token is missing {permissions.missing_scopes.length} required permission{permissions.missing_scopes.length !== 1 ? 's' : ''}:
                <span className="font-medium ml-1">
                  {permissions.missing_scopes.join(', ')}
                </span>
              </p>
              <p className="text-sm">
                Some features may not work properly. Consider generating a new token with all required permissions.
              </p>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Token Generation Guide */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Generate Optimal Token</CardTitle>
          <CardDescription>
            Create a GitHub personal access token with all required permissions
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <h4 className="font-medium">Required Permissions:</h4>
            <div className="flex flex-wrap gap-1">
              {Object.keys(SCOPE_INFO).map((scope) => (
                <Badge key={scope} variant="secondary" className="text-xs">
                  {scope}
                </Badge>
              ))}
            </div>
          </div>
          
          <div className="flex gap-2">
            <Button
              asChild
              className="flex-1"
            >
              <a href={generateTokenUrl()} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4 mr-2" />
                Generate GitHub Token
              </a>
            </Button>
            <Button
              variant="outline"
              onClick={() => copyToClipboard(generateTokenUrl())}
            >
              <Copy className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="text-xs text-muted-foreground">
            <p className="font-medium mb-1">Instructions:</p>
            <ol className="list-decimal list-inside space-y-1">
              <li>Click "Generate GitHub Token" to open GitHub settings</li>
              <li>Set expiration date (recommended: 90 days)</li>
              <li>Ensure all required scopes are selected</li>
              <li>Click "Generate token" and copy the result</li>
              <li>Return here and update your token</li>
            </ol>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 