'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { EyeIcon, CrossIcon, CheckCircleFillIcon } from '@/components/icons';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';

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
  if (status === 'indexed') {
    return (
      <span className="text-green-500">
        <CheckCircleFillIcon size={16} />
      </span>
    );
  }
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
  const [error, setError] = useState<string | null>(null);
  const [isPrefilled, setIsPrefilled] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [repoDetails, setRepoDetails] = useState<RepositoryDetails | null>(null);

  // Fetch repository details when the dialog opens
  useEffect(() => {
    if (open && session?.user?.selectedSpace?.processId) {
      fetchRepositoryDetails();
    } else if (!open) {
      // Reset editing state when dialog closes
      setIsEditing(false);
    }
  }, [open, session?.user?.selectedSpace?.processId]);

  // Function to fetch repository details
  const fetchRepositoryDetails = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch('/api/repo');
      const data = await response.json();
      
      if (response.ok && data.connected && data.url) {
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
          indexing_completed: data.indexing_completed
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

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const renderConnectedRepoInfo = () => {
    if (!repoDetails) return null;
    
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
          <div className="flex items-center gap-2">
            <StatusIcon status={repoDetails.status} />
            <span className="capitalize">{repoDetails.status}</span>
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
        
        <div className="flex flex-col gap-1">
          <div className="font-semibold">Git Information</div>
          <div className="grid grid-cols-2 gap-x-2 text-muted-foreground">
            <span>Branch:</span>
            <span>{repoDetails.branch || 'N/A'}</span>
            <span>Commit:</span>
            <span className="truncate">{repoDetails.commit_sha || 'N/A'}</span>
          </div>
        </div>
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
        // Update the space with the knowledge base ID
        const updateResponse = await fetch('/api/spaces/update', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            spaceId: session.user.selectedSpace.id,
            knowledgeBaseId: knowledgeBaseId,
            processId: data.process_id || null,
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
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent>
        <SheetHeader>
          <SheetTitle>Connect Repository</SheetTitle>
          <SheetDescription>
            Connect a code repository to enhance your chat experience.
          </SheetDescription>
        </SheetHeader>
        
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
            </div>
            
            {error && (
              <div className="text-sm text-red-500 flex items-center gap-1">
                <CrossIcon size={12} />
                {error}
              </div>
            )}
          </form>
        )}
        
        <SheetFooter className="mt-4">
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
              type="submit"
              onClick={isEditing ? handleSubmit : undefined}
              disabled={isSubmitting || isLoading}
            >
              {isSubmitting ? 'Connecting...' : 'Connect Repository'}
            </Button>
          )}
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
} 