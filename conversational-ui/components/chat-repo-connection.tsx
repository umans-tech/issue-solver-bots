'use client';

import { useState, useEffect } from 'react';
import { useSession } from 'next-auth/react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { EyeIcon, CheckCircleFillIcon, CrossIcon } from '@/components/icons';
import { useProcessStatus } from '@/hooks/use-process-status';

interface ChatRepoConnectionProps {
  onConnectionStart?: () => void;
  onConnectionComplete?: (success: boolean, details?: any) => void;
  onStatusUpdate?: (status: string, message: string) => void;
  isHumanInTheLoop?: boolean; // When true, don't make API call, just pass form data
}

interface RepositoryDetails {
  url: string;
  status: string;
  knowledge_base_id: string;
  process_id: string;
  error?: boolean;
  errorType?: string;
  errorMessage?: string;
}

export function ChatRepoConnection({
  onConnectionStart,
  onConnectionComplete,
  onStatusUpdate,
  isHumanInTheLoop,
}: ChatRepoConnectionProps) {
  const { data: session, update: updateSession } = useSession();
  const [repoUrl, setRepoUrl] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [showToken, setShowToken] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'connecting' | 'success' | 'error'>('idle');

  const processId = session?.user?.selectedSpace?.processId;
  const liveProcessStatus = useProcessStatus(processId);

  // Handle status updates
  useEffect(() => {
    if (liveProcessStatus && onStatusUpdate) {
      const statusMessages = {
        indexing: 'Repository is being indexed...',
        indexed: 'Repository indexing completed!',
        connected: 'Repository connected successfully!',
      };
      
      const message = statusMessages[liveProcessStatus as keyof typeof statusMessages] || `Status: ${liveProcessStatus}`;
      onStatusUpdate(liveProcessStatus, message);
    }
  }, [liveProcessStatus, onStatusUpdate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!repoUrl) {
      setError('Repository URL is required');
      return;
    }

    // Access token is optional for public repositories
    
    setError(null);
    setIsSubmitting(true);
    setConnectionStatus('connecting');
    onConnectionStart?.();
    
    try {
      // Check session validity
      if (!session?.user?.id || !session?.user?.selectedSpace?.id) {
        await updateSession();
        
        if (!session?.user?.id || !session?.user?.selectedSpace?.id) {
          throw new Error('Session data is incomplete. Please reload the page and try again.');
        }
      }
      
      const payload = {
        repoUrl,
        accessToken,
        userId: session.user.id,
        spaceId: session.user.selectedSpace.id,
      };
      
      const response = await fetch('/api/repo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        if (data.errorType && data.errorMessage) {
          const errorObj = new Error(data.errorMessage);
          (errorObj as any).type = data.errorType;
          throw errorObj;
        }
        throw new Error(data.error || 'Failed to connect repository');
      }
      
      // Extract process_id from events if needed
      if (data.status?.toLowerCase() === 'connected' && !data.process_id && data.events && data.events[0]) {
        data.process_id = data.events[0].process_id;
      }
      
      const knowledgeBaseId = data.knowledgeBaseId || data.knowledge_base_id;
      
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
        
        const updatedSpace = {
          ...session.user.selectedSpace,
          knowledgeBaseId: knowledgeBaseId,
          processId: data.process_id || null,
        };
        
        await updateSession({
          user: {
            ...session.user,
            selectedSpace: updatedSpace,
            knowledgeBaseId: knowledgeBaseId
          }
        });
      } else {
        throw new Error('No knowledge base ID received from the server');
      }
      
      setConnectionStatus('success');
      
      // Pass all connection details to parent
      const connectionResult = {
        url: repoUrl,
        accessToken,
        userId: session.user.id,
        spaceId: session.user.selectedSpace.id,
        knowledgeBaseId,
        processId: data.process_id,
        status: data.status
      };
      
      console.log('🚀 ChatRepoConnection calling onConnectionComplete with:', connectionResult);
      onConnectionComplete?.(true, connectionResult);
      
      // Clear form
      setRepoUrl('');
      setAccessToken('');
      
    } catch (err: any) {
      console.error("Error in repository connection:", err);
      setConnectionStatus('error');
      
      if (err instanceof Error && (err as any).type) {
        const errorMessage = `Connection failed: ${err.message}`;
        setError(errorMessage);
        onConnectionComplete?.(false, {
          error: true,
          errorType: (err as any).type,
          errorMessage: err.message,
          url: repoUrl
        });
      } else {
        const errorMessage = err instanceof Error ? err.message : 'An error occurred';
        setError(errorMessage);
        onConnectionComplete?.(false, { 
          error: true, 
          errorMessage,
          url: repoUrl
        });
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="gap-4 bg-muted p-6 shadow-lg transition ease-in-out border rounded-lg max-w-sm mx-auto">
      <div className="mb-4">
        <h3 className="font-semibold text-lg">Connect Repository</h3>
        <p className="text-sm text-muted-foreground">
          Connect a code repository to enhance your chat experience.
        </p>
      </div>
      
      <form onSubmit={handleSubmit} className="space-y-6 py-6">
        <div className="space-y-2">
          <Label htmlFor="repoUrl">Repository URL</Label>
          <Input
            id="repoUrl"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/username/repo"
            disabled={isSubmitting}
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
              disabled={isSubmitting}
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="absolute right-2 top-1/2 -translate-y-1/2 h-7 w-7"
              onClick={() => setShowToken(!showToken)}
              disabled={isSubmitting}
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
      
      <div className="mt-4">
        <Button
          type="button"
          onClick={handleSubmit}
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Connecting...' : 'Connect Repository'}
        </Button>
      </div>
    </div>
  );
} 