'use client';

import { useState } from 'react';
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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!repoUrl) {
      setError('Repository URL is required');
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
          
          <div className="space-y-2">
            <Label htmlFor="accessToken">Access Token</Label>
            <div className="relative">
              <Input
                id="accessToken"
                type={showToken ? 'text' : 'password'}
                value={accessToken}
                onChange={(e) => setAccessToken(e.target.value)}
                placeholder="ghp_xxxxxxxxxxxx"
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