'use client';

import { useState } from 'react';
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
    
    if (!accessToken) {
      setError('Access token is required');
      return;
    }
    
    setError(null);
    setIsSubmitting(true);
    
    try {
      // Call our Next.js API route instead of directly calling the CUDU API
      const response = await fetch('/api/repo', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repoUrl,
          accessToken,
        }),
      });
      
      // Get the response data
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || 'Failed to connect repository');
      }
      
      // Directly save the knowledge base ID to localStorage as a raw string
      if (data.knowledge_base_id) {
        localStorage.setItem('knowledge_base_id', data.knowledge_base_id);
        console.log('Knowledge base ID saved:', data.knowledge_base_id);
      }
      
      // Success
      setRepoUrl('');
      setAccessToken('');
      onOpenChange(false);
    } catch (err) {
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