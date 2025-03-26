'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { EyeIcon, CrossIcon } from '@/components/icons';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Checkbox } from '@/components/ui/checkbox';

// Utility function to determine git provider from URL
const getGitProviderFromUrl = (url: string): 'git' | 'github' | 'gitlab' | 'azure' | 'bitbucket' => {
  if (!url) return 'git';
  
  const lowerUrl = url.toLowerCase();
  
  if (lowerUrl.includes('github.com')) {
    return 'github';
  } else if (lowerUrl.includes('gitlab.com')) {
    return 'gitlab';
  } else if (lowerUrl.includes('dev.azure.com') || lowerUrl.includes('visualstudio.com')) {
    return 'azure';
  } else if (lowerUrl.includes('bitbucket.org')) {
    return 'bitbucket';
  }
  
  return 'git'; // Default fallback
};

interface RepoConnectionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function RepoConnectionDialog({
  open,
  onOpenChange,
}: RepoConnectionDialogProps) {
  const { data: session, update: updateSession } = useSession();
  const [repoUrl, setRepoUrl] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [showToken, setShowToken] = useState(false);
  const [isPublicRepo, setIsPublicRepo] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [gitProvider, setGitProvider] = useState<'git' | 'github' | 'gitlab' | 'azure' | 'bitbucket'>('git');

  // Update the git provider when the URL changes
  useEffect(() => {
    setGitProvider(getGitProviderFromUrl(repoUrl));
  }, [repoUrl]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!repoUrl) {
      setError('Repository URL is required');
      return;
    }
    
    if (!isPublicRepo && !accessToken) {
      setError('Access token is required for private repositories');
      return;
    }
    
    setError(null);
    setIsSubmitting(true);
    
    try {
      console.log("Starting repository connection...");
      
      // Check if we have a valid session with a selected space
      if (!session?.user?.id || !session?.user?.selectedSpace?.id) {
        console.log("Session data incomplete, refreshing session...");
        // Try to refresh the session to get the latest data
        await updateSession();
        // Small delay to ensure session is updated
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      // If we still don't have a valid session with space, log and show error
      if (!session?.user?.id || !session?.user?.selectedSpace?.id) {
        console.error("Invalid session: Missing user ID or selected space", {
          userId: session?.user?.id,
          spaceId: session?.user?.selectedSpace?.id
        });
        throw new Error('Session data is incomplete. Please reload the page and try again.');
      }
      
      // Gather data for the API call including user and space info
      const payload = {
        repoUrl,
        // Use empty string for access token if it's a public repo
        accessToken: isPublicRepo ? "" : accessToken,
        userId: session.user.id,
        spaceId: session.user.selectedSpace.id,
      };
      
      console.log("Payload prepared:", {
        ...payload,
        accessToken: isPublicRepo ? "(empty - public repo)" : "***REDACTED***"
      });
      
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
      
      console.log("API response received:", data);
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to connect repository');
      }
      
      // Log important fields from response to debug
      console.log("Critical fields from response:", {
        knowledge_base_id: data.knowledge_base_id || 'NOT PROVIDED',
        process_id: data.process_id || 'NOT PROVIDED',
        status: data.status || 'NOT PROVIDED'
      });
      
      // When we get 'connected' status from the CUDU API, we should make sure process_id is passed to the session
      if (data.status?.toLowerCase() === 'connected' && !data.process_id && data.events && data.events[0]) {
        // Try to extract the process_id from events if it's not at the top level
        console.log("Status is 'connected' but no top-level process_id, looking in events");
        data.process_id = data.events[0].process_id;
        console.log("Extracted process_id from events:", data.process_id);
      }
      
      // If we have the space info, update the space with the knowledge base ID
      if (session?.user?.id && session?.user?.selectedSpace?.id && data.knowledge_base_id) {
        console.log("Updating space with knowledge base ID:", data.knowledge_base_id);
        console.log("Process ID being sent:", data.process_id);
        
        // Update the space with the knowledge base ID
        const updateResponse = await fetch('/api/spaces/update', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            spaceId: session.user.selectedSpace.id,
            knowledgeBaseId: data.knowledge_base_id,
            // If there's a process_id, it means indexing is in progress - ensure it's sent
            processId: data.process_id || null,
            // Include the repository URL so we can determine the provider later
            repoUrl: repoUrl
          }),
        });
        
        if (!updateResponse.ok) {
          console.error('Failed to update space with knowledge base ID');
        } else {
          console.log("Space updated successfully, now updating session");
          
          // Create the updated space info
          const updatedSpace = {
            ...session.user.selectedSpace,
            knowledgeBaseId: data.knowledge_base_id,
            processId: data.process_id || null,
            // Add repository URL for provider detection
            repoUrl: repoUrl
          };
          
          console.log("Updated space object:", updatedSpace);
          
          try {
            // First, update the local session with the new data
            const updatedUser = {
              ...session.user,
              selectedSpace: updatedSpace
            };
            
            console.log("Updating local session with user data:", {
              email: updatedUser.email,
              id: updatedUser.id,
              selectedSpace: {
                ...updatedSpace,
                repoUrl: repoUrl // Explicitly log this for debugging
              }
            });
            
            // Update the local session first
            await updateSession({
              user: updatedUser
            });
            console.log("Local session updated successfully");
            
            // Then, explicitly trigger a refresh from the server session data
            // Using POST to ensure it's not cached and to work around any CORS issues
            console.log("Forcing complete session refresh from server...");
            const sessionResponse = await fetch('/api/auth/session', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'no-cache'
              }
            });
            
            if (sessionResponse.ok) {
              const freshSession = await sessionResponse.json();
              console.log("Fresh session data from server:", {
                knowledgeBaseId: freshSession?.user?.selectedSpace?.knowledgeBaseId,
                processId: freshSession?.user?.selectedSpace?.processId
              });

              // Apply the fresh session data
              await updateSession(freshSession);
              console.log("Session fully refreshed with server data");
              
              // Delay to ensure session updates are processed
              await new Promise(resolve => setTimeout(resolve, 1500));
              
              // Reload the page with a unique query parameter to force a fresh render
              const currentPath = window.location.pathname;
              const timestamp = Date.now();
              window.location.href = `${currentPath}?refresh=${timestamp}`;
            } else {
              console.error("Failed to refresh session from server:", sessionResponse.statusText);
              
              // Even if refresh fails, still reload the page to get fresh data
              const currentPath = window.location.pathname;
              const timestamp = Date.now();
              window.location.href = `${currentPath}?refresh=${timestamp}`;
            }
          } catch (sessionError) {
            console.error("Error updating session:", sessionError);
            
            // Even if there's an error, reload the page to try to get fresh data
            const currentPath = window.location.pathname;
            const timestamp = Date.now();
            window.location.href = `${currentPath}?refresh=${timestamp}`;
          }
        }
      } else {
        console.warn("Cannot update space - missing required data:", {
          userId: session?.user?.id,
          spaceId: session?.user?.selectedSpace?.id,
          knowledgeBaseId: data.knowledge_base_id
        });
      }
      
      // Success
      setRepoUrl('');
      setAccessToken('');
      setIsPublicRepo(false);
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
        
        <form onSubmit={handleSubmit} className="space-y-6 py-6">
          <div className="space-y-2">
            <Label htmlFor="repoUrl">Repository URL</Label>
            <Input
              id="repoUrl"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/username/repo"
            />
          </div>
          
          <div className="flex items-center space-x-2 pt-2">
            <Checkbox 
              id="isPublicRepo" 
              checked={isPublicRepo}
              onCheckedChange={(checked: boolean | 'indeterminate') => {
                setIsPublicRepo(checked === true);
                if (checked === true) {
                  setError(null);
                }
              }}
            />
            <Label 
              htmlFor="isPublicRepo" 
              className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
            >
              This is a public repository (no access token needed)
            </Label>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="accessToken">
              {isPublicRepo ? 'Access Token (optional)' : 'Access Token'}
            </Label>
            <div className="relative">
              <Input
                id="accessToken"
                type={showToken ? 'text' : 'password'}
                value={accessToken}
                onChange={(e) => setAccessToken(e.target.value)}
                placeholder={isPublicRepo ? "(Optional for public repos)" : "ghp_xxxxxxxxxxxx"}
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-2 top-1/2 -translate-y-1/2 h-7 w-7"
                onClick={() => setShowToken(!showToken)}
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
          
          <SheetFooter>
            <Button
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Connecting...' : 'Connect Repository'}
            </Button>
          </SheetFooter>
        </form>
      </SheetContent>
    </Sheet>
  );
} 