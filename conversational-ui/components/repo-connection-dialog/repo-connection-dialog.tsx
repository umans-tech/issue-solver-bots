'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { EyeIcon, CrossIcon, CheckCircleFillIcon, CopyIcon, RedoIcon, ClockRewind, AlertCircle } from '@/components/icons';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { useProcessStatus } from '@/hooks/use-process-status';
import { TokenPermissionsDisplay } from '@/components/token-permissions-display';
import { ProactiveTokenGenerator } from '@/components/proactive-token-generator';
import { EnvironmentSetupDialog } from '@/components/environment-setup-dialog';

// Simple clock icon component
const ClockIcon = ({ size = 16 }: { size?: number }) => (
  <svg
    height={size}
    width={size}
    viewBox="0 0 16 16"
    style={{ color: 'currentcolor' }}
  >
    <circle cx="8" cy="8" r="7" stroke="currentColor" fill="none" strokeWidth="1.5" />
    <path d="M8 4.5V8H11.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
  </svg>
);

// Status display with proper icons
const StatusIcon = ({ status }: { status: string }) => {
  // Define status indicator colors - match with GitIcon's colors
  const statusColors = {
    indexing: '#FA75AA', // Pink color from Umans logo for indexing
    indexed: '#FA75AA' // Pink color from Umans logo
  };
  
  if (status === 'indexed') {
    return (
      <span className="text-green-500">
        <CheckCircleFillIcon size={16} />
      </span>
    );
  }
  
  // Use the same animated indicator as GitIcon for indexing status
  if (status === 'indexing' || status === 'connected') {
    return (
      <div className="relative inline-flex items-center justify-center">
        <div
          className="w-[14px] h-[14px] rounded-full animate-pulse"
          style={{ backgroundColor: statusColors.indexing, opacity: 0.6 }}
        />
      </div>
    );
  }
  
  // Fallback for unknown status
  return (
    <span className="text-amber-500">
      <ClockIcon size={16} />
    </span>
  );
};

interface RepoConnectionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface RepositoryDetails {
  url: string;
  status: string;
  knowledge_base_id: string;
  process_id: string;
  branch?: string;
  commit_sha?: string;
  indexing_started?: string;
  indexing_completed?: string;
  error?: boolean;
  errorType?: string;
  errorMessage?: string;
  token_permissions?: any;
}

export function RepoConnectionDialog({
  open,
  onOpenChange,
}: RepoConnectionDialogProps) {
  const { data: session, update: updateSession } = useSession();
  const [repoUrl, setRepoUrl] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [showToken, setShowToken] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSyncing, setIsSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPrefilled, setIsPrefilled] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [repoDetails, setRepoDetails] = useState<RepositoryDetails | null>(null);
  const [isRotatingToken, setIsRotatingToken] = useState(false);
  const [newAccessToken, setNewAccessToken] = useState('');
  const [showNewToken, setShowNewToken] = useState(false);
  const [envDialogOpen, setEnvDialogOpen] = useState(false);
  
  // Get the process id from session
  const processId = session?.user?.selectedSpace?.processId;
  
  // Use the same hook that the chat header uses to get live status updates
  const liveProcessStatus = useProcessStatus(processId);

  // Fetch repository details when the dialog opens or session changes
  useEffect(() => {
    if (open && processId) {
      fetchRepositoryDetails();
    } else if (!open) {
      // Reset editing state when dialog closes
      setIsEditing(false);
      setIsRotatingToken(false);
      setNewAccessToken('');
      setShowNewToken(false);
    }
  }, [open, processId]);

  // Update local status when process status changes
  useEffect(() => {
    if (open && repoDetails && liveProcessStatus) {
      // Only update if status actually changed
      if (liveProcessStatus !== repoDetails.status) {
        console.log(`Status updated from process hook: ${repoDetails.status} -> ${liveProcessStatus}`);
        
        setRepoDetails(prev => {
          if (!prev) return null;
          return {
            ...prev,
            status: liveProcessStatus
          };
        });
      }
    }
  }, [open, repoDetails, liveProcessStatus]);

  // Function to fetch repository details
  const fetchRepositoryDetails = async () => {
    if (!processId) return;
    
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch('/api/repo');
      const data = await response.json();
      
      // Check if we received an error response
      if (response.ok && data.error === true) {
        console.log(`Repository connection failed: ${data.errorMessage}`);
        setIsPrefilled(true);
        setIsEditing(false);
        
        // Save error details
        setRepoDetails({
          url: data.url || '',
          status: 'failed',
          knowledge_base_id: data.knowledge_base_id || '',
          process_id: data.process_id || processId,
          error: true,
          errorType: data.errorType,
          errorMessage: data.errorMessage
        });
      } else if (response.ok && data.connected && data.url) {
        // Prefill the form with the repository URL
        setRepoUrl(data.url);
        // Set placeholder stars for the access token
        setAccessToken('************');
        // Mark as prefilled
        setIsPrefilled(true);
        // Start in non-editing mode
        setIsEditing(false);
        
        // Save comprehensive repo details for display
        setRepoDetails({
          url: data.url,
          status: data.status || 'unknown',
          knowledge_base_id: data.knowledge_base_id,
          process_id: data.process_id,
          branch: data.branch,
          commit_sha: data.commit_sha,
          indexing_started: data.indexing_started,
          indexing_completed: data.indexing_completed,
          token_permissions: data.token_permissions
        });
      } else {
        // No existing repository, enable editing by default
        setIsPrefilled(false);
        setIsEditing(true);
        setRepoDetails(null);
      }
    } catch (err) {
      console.error('Error fetching repository details:', err);
      // Don't set an error to the user for this, just log it
      // Enable editing in case of error
      setIsEditing(true);
      setRepoDetails(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChangeRepository = () => {
    setIsEditing(true);
    setRepoUrl('');
    setAccessToken('');
    setError(null);
  };

  // Function to handle token rotation
  const handleTokenRotation = async () => {
    if (!newAccessToken.trim()) {
      toast.error('Please enter a new access token');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const response = await fetch('/api/repo/token', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          accessToken: newAccessToken,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Failed to rotate token');
      }

      toast.success('Access token updated successfully!');
      setIsRotatingToken(false);
      setNewAccessToken('');
      setShowNewToken(false);
      
      if (data.token_permissions) {
        setRepoDetails(prev => prev ? {
          ...prev,
          token_permissions: data.token_permissions
        } : null);
      }
    } catch (err) {
      console.error('Error updating token:', err);
      toast.error(err instanceof Error ? err.message : 'Failed to update token');
    } finally {
      setIsSubmitting(false);
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  // Function to sync repository
  const handleSyncRepository = async () => {
    if (!repoDetails?.knowledge_base_id) {
      toast.error('No repository to sync');
      return;
    }

    try {
      setIsSyncing(true);
      setError(null);
      
      const response = await fetch('/api/repo/sync', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to sync repository');
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Set a temporary visual feedback by updating the status locally
        setRepoDetails(prev => prev ? {
          ...prev,
          status: 'indexing'
        } : null);
        
        // First, close the dialog with proper animation
        onOpenChange(false);
        
        // After the dialog closes and a small delay, reload the page
        // This ensures both proper dialog animation and fresh data on reload
        setTimeout(() => {
          window.location.reload();
        }, 300); // Give dialog time to animate out
      } else {
        throw new Error(data.message || 'Failed to sync repository');
      }
    } catch (err) {
      console.error('Error syncing repository:', err);
      toast.error(err instanceof Error ? err.message : 'Failed to sync repository');
    } finally {
      setIsSyncing(false);
    }
  };

  const renderConnectedRepoInfo = () => {
    if (!repoDetails) return null;
    
    const copyCommitSha = () => {
      if (repoDetails.commit_sha) {
        navigator.clipboard.writeText(repoDetails.commit_sha);
        toast.success('Commit SHA copied to clipboard!');
      }
    };
    
    // If we have an error, show an error message instead of repository details
    if (repoDetails.error) {
      return (
        <div className="space-y-4 py-4 text-sm">
          <div className="flex flex-col gap-1 border-b pb-3">
            <div className="font-semibold">Repository Connection Failed</div>
            <div className="flex items-center gap-2 text-muted-foreground break-all">
              <span>{repoDetails.url}</span>
            </div>
          </div>
          
          <div className="flex flex-col gap-1 pb-3">
            <div className="font-semibold">Error Details</div>
            <div className="flex items-center text-red-500 gap-2">
              <AlertCircle size={16} />
              <span>{repoDetails.errorMessage || 'Unknown error occurred'}</span>
            </div>
            <div className="text-muted-foreground text-xs mt-2">
              {repoDetails.errorType === 'authentication_failed' && (
                <p>Please check your access token and make sure it has the necessary permissions to access this repository.</p>
              )}
              {repoDetails.errorType === 'repository_not_found' && (
                <p>The repository URL could not be found. Please verify that the URL is correct.</p>
              )}
              {repoDetails.errorType === 'repository_unavailable' && (
                <p>Could not connect to the repository. Please check your internet connection and try again.</p>
              )}
              {repoDetails.errorType === 'permission_denied' && (
                <p>You don't have permission to access this repository. Please check your access rights.</p>
              )}
            </div>
          </div>
          
          <div className="flex flex-col gap-1 border-t pt-3">
            <div className="font-semibold">Recommendation</div>
            <div className="text-muted-foreground">
              <p>Click "Change Repository" below to edit your repository connection settings.</p>
            </div>
          </div>
        </div>
      );
    }
    
    return (
      <div className="space-y-4 py-4 text-sm">
        <div className="flex flex-col gap-1 border-b pb-3">
          <div className="font-semibold">Connected Repository</div>
          <div className="flex items-center gap-2 text-muted-foreground break-all">
            <span>{repoDetails.url}</span>
          </div>
        </div>
        
        <div className="flex flex-col gap-1 border-b pb-3">
          <div className="font-semibold">Indexation Status</div>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <StatusIcon status={repoDetails.status} />
              <span className="capitalize">
                {repoDetails.status === 'connected' ? 'indexing' : repoDetails.status}
              </span>
            </div>
            
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="h-8 px-3 flex items-center gap-1"
              onClick={handleSyncRepository}
              disabled={isSyncing || repoDetails.status === 'indexing' || repoDetails.status === 'connected' || repoDetails.status === 'failed'}
            >
              <div className={isSyncing ? 'animate-spin' : ''}>
                <ClockRewind size={14} />
              </div>
              <span>Sync Latest</span>
            </Button>
          </div>
        </div>
        
        <div className="flex flex-col gap-1 border-b pb-3">
          <div className="font-semibold">Indexation Times</div>
          <div className="grid grid-cols-2 gap-x-2 text-muted-foreground">
            <span>Started:</span>
            <span>{formatDate(repoDetails.indexing_started)}</span>
            <span>Completed:</span>
            <span>{formatDate(repoDetails.indexing_completed)}</span>
          </div>
        </div>
        
        <div className="flex flex-col gap-1 border-b pb-3">
          <div className="font-semibold">Git Information</div>
          <div className="grid grid-cols-2 gap-x-2 text-muted-foreground">
            <span>Branch:</span>
            <span>{repoDetails.branch || 'N/A'}</span>
            <span>Commit:</span>
            <div className="flex items-center gap-1">
              <span className="truncate">{repoDetails.commit_sha || 'N/A'}</span>
              {repoDetails.commit_sha && (
                <Button
                  onClick={copyCommitSha}
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="h-5 w-5 p-0.5 hover:bg-muted rounded-sm"
                >
                  <CopyIcon size={14} />
                  <span className="sr-only">Copy commit SHA</span>
                </Button>
              )}
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-1">
          <div className="font-semibold">Access Token</div>
          {isRotatingToken ? (
            <div className="space-y-3">
              <div className="text-sm text-muted-foreground">
                Enter your new access token:
              </div>
              <div className="relative">
                <Input
                  type={showNewToken ? 'text' : 'password'}
                  value={newAccessToken}
                  onChange={(e) => setNewAccessToken(e.target.value)}
                  placeholder="ghp_xxxxxxxxxxxx"
                  disabled={isSubmitting}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  className="absolute right-2 top-1/2 -translate-y-1/2 h-7 w-7"
                  onClick={() => setShowNewToken(!showNewToken)}
                  disabled={isSubmitting}
                >
                  <EyeIcon size={16} />
                  <span className="sr-only">
                    {showNewToken ? 'Hide token' : 'Show token'}
                  </span>
                </Button>
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  size="sm"
                  onClick={handleTokenRotation}
                  disabled={isSubmitting || !newAccessToken.trim()}
                >
                  {isSubmitting ? 'Updating...' : 'Update Token'}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setIsRotatingToken(false);
                    setNewAccessToken('');
                    setShowNewToken(false);
                  }}
                  disabled={isSubmitting}
                >
                  Cancel
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">************</span>
              <Button
                type="button"
                size="sm"
                variant="outline"
                className="h-8 px-3 flex items-center gap-1"
                onClick={() => setIsRotatingToken(true)}
                disabled={isSubmitting}
              >
                <RedoIcon size={14} />
                <span>Update Token</span>
              </Button>
            </div>
          )}
        </div>

        {/* Token Permissions Display */}
        {repoDetails.token_permissions && (
          <div className="border-t pt-4 mt-4">
            <TokenPermissionsDisplay 
              permissions={repoDetails.token_permissions}
              repositoryUrl={repoDetails.url}
            />
          </div>
        )}
      </div>
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!repoUrl) {
      setError('Repository URL is required');
      return;
    }

    // Check if the access token is the placeholder stars and show an error
    if (accessToken === '************') {
      setError('Please enter your access token');
      return;
    }
    
    setError(null);
    setIsSubmitting(true);
    
    try {
      // Check if we have a valid session with a selected space
      if (!session?.user?.id || !session?.user?.selectedSpace?.id) {
        // Try to refresh the session to get the latest data
        await updateSession();
        
        // If we still don't have valid session data, show error
        if (!session?.user?.id || !session?.user?.selectedSpace?.id) {
          throw new Error('Session data is incomplete. Please reload the page and try again.');
        }
      }
      
      // Gather data for the API call including user and space info
      const payload = {
        repoUrl,
        accessToken,
        userId: session.user.id,
        spaceId: session.user.selectedSpace.id,
      };
      
      // Call our Next.js API route
      const response = await fetch('/api/repo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      
      // Get the response data
      const data = await response.json();
      
      if (!response.ok) {
        // Check if we have detailed error information
        if (data.errorType && data.errorMessage) {
          // Create error object with type information
          const errorObj = new Error(data.errorMessage);
          // @ts-ignore - add custom properties
          errorObj.type = data.errorType;
          throw errorObj;
        }
        
        throw new Error(data.error || 'Failed to connect repository');
      }
      
      // Extract process_id from events if needed
      if (data.status?.toLowerCase() === 'connected' && !data.process_id && data.events && data.events[0]) {
        data.process_id = data.events[0].process_id;
      }
      
      // Get the correct knowledge base ID, handling both formats
      const knowledgeBaseId = data.knowledgeBaseId || data.knowledge_base_id;
      
      // If we have the knowledge base ID, update the space
      if (knowledgeBaseId) {
        // Update the space with the knowledge base ID and connected repo URL
        const updateResponse = await fetch('/api/spaces/update', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            spaceId: session.user.selectedSpace.id,
            knowledgeBaseId: knowledgeBaseId,
            processId: data.process_id || null,
            connectedRepoUrl: repoUrl,
          }),
        });
        
        if (!updateResponse.ok) {
          throw new Error('Failed to update space with knowledge base ID');
        }
        
        // Create properly structured updated space
        const updatedSpace = {
          ...session.user.selectedSpace,
          knowledgeBaseId: knowledgeBaseId,
          processId: data.process_id || null,
          connectedRepoUrl: repoUrl,
        };
        
        // Update the session with the new space data
        await updateSession({
          user: {
            ...session.user,
            selectedSpace: updatedSpace,
            // Also add at root level for direct access by codebase search
            knowledgeBaseId: knowledgeBaseId
          }
        });
        
        // Reload the page to ensure fresh data
        window.location.reload();
      } else {
        throw new Error('No knowledge base ID received from the server');
      }
      
      // Success
      setRepoUrl('');
      setAccessToken('');
      onOpenChange(false);
    } catch (err) {
      console.error("Error in repository connection:", err);
      
      // Check if we have a typed error from our API
      // @ts-ignore - check for custom properties
      if (err instanceof Error && err.type) {
        setRepoDetails({
          // @ts-ignore - we know these properties exist
          url: repoUrl,
          status: 'failed',
          knowledge_base_id: '',
          process_id: '',
          error: true,
          // @ts-ignore - we know these properties exist
          errorType: err.type,
          errorMessage: err.message
        });
        
        // Show the error in the error UI section rather than edit mode
        setIsPrefilled(true);
        setIsEditing(false);
      } else {
        // Standard error handling for other error types
        setError(err instanceof Error ? err.message : 'An error occurred');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="flex flex-col max-h-screen">
        <SheetHeader className="flex-shrink-0">
          <SheetTitle>Connect Repository</SheetTitle>
          <SheetDescription>
            Connect a code repository to enhance your chat experience.
          </SheetDescription>
        </SheetHeader>
        
        <div className="flex-1 overflow-y-auto px-1">
          {isLoading ? (
            <div className="py-8 text-center">
              <div className="text-sm text-muted-foreground">
                Loading repository information...
              </div>
            </div>
          ) : isPrefilled && !isEditing ? (
            // Display comprehensive repository information
            renderConnectedRepoInfo()
          ) : (
            // Display the form for editing/adding repository
            <form onSubmit={handleSubmit} className="space-y-6 py-6">
              <div className="space-y-2">
                <Label htmlFor="repoUrl">Repository URL</Label>
                <Input
                  id="repoUrl"
                  value={repoUrl}
                  onChange={(e) => setRepoUrl(e.target.value)}
                  placeholder="https://github.com/username/repo"
                  disabled={isLoading}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="accessToken">Access Token</Label>
                <div className="relative">
                  <Input
                    id="accessToken"
                    type={showToken ? 'text' : 'password'}
                    value={accessToken}
                    onChange={(e) => setAccessToken(e.target.value)}
                    placeholder="ghp_xxxxxxxxxxxx"
                    disabled={isLoading}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="absolute right-2 top-1/2 -translate-y-1/2 h-7 w-7"
                    onClick={() => setShowToken(!showToken)}
                    disabled={isLoading}
                  >
                    <EyeIcon size={16} />
                    <span className="sr-only">
                      {showToken ? 'Hide token' : 'Show token'}
                    </span>
                  </Button>
                </div>
                
                {/* Proactive Token Generator */}
                {repoUrl && (
                  <ProactiveTokenGenerator
                    repositoryUrl={repoUrl}
                    className="mt-2 p-2 bg-muted/30 rounded-md border"
                  />
                )}
              </div>
              
              {error && (
                <div className="text-sm text-red-500 flex items-center gap-1">
                  <CrossIcon size={12} />
                  {error}
                </div>
              )}
            </form>
          )}
        </div>
        
        <SheetFooter className="flex-shrink-0 mt-4">
          {isPrefilled && !isEditing ? (
            <Button
              type="button"
              onClick={handleChangeRepository}
              disabled={isLoading}
            >
              Change Repository
            </Button>
          ) : (
            <Button
              type="button"
              onClick={handleSubmit}
              disabled={isSubmitting || isLoading}
            >
              {isSubmitting ? 'Connecting...' : 'Connect Repository'}
            </Button>
          )}
          {repoDetails?.knowledge_base_id && (
            <Button
              type="button"
              variant="outline"
              onClick={() => setEnvDialogOpen(true)}
              disabled={isLoading}
            >
              Environment setup
            </Button>
          )}
        </SheetFooter>
      </SheetContent>
      {/* Environment setup dialog */}
      <EnvironmentSetupDialog
        open={envDialogOpen}
        onOpenChange={setEnvDialogOpen}
        knowledgeBaseId={repoDetails?.knowledge_base_id}
      />
    </Sheet>
  );
} 