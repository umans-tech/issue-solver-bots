'use client';

import { useEffect, useState } from 'react';
import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';

interface AutoDocPublishDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  defaultTitle: string;
  defaultPath: string;
  onPublish: (payload: { title: string; path: string }) => void;
}

export function AutoDocPublishDialog({
  open,
  onOpenChange,
  defaultTitle,
  defaultPath,
  onPublish,
}: AutoDocPublishDialogProps) {
  const [title, setTitle] = useState(defaultTitle);
  const [path, setPath] = useState(defaultPath);

  useEffect(() => {
    if (!open) return;
    setTitle(defaultTitle);
    setPath(defaultPath);
  }, [defaultPath, defaultTitle, open]);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    onPublish({ title: title.trim(), path: path.trim() });
    onOpenChange(false);
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="sm:max-w-[520px]">
        <AlertDialogHeader>
          <AlertDialogTitle>Publish to Docs</AlertDialogTitle>
        </AlertDialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="auto-doc-title">Title</Label>
            <Input
              id="auto-doc-title"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Doc title"
              autoFocus
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="auto-doc-path">Doc path</Label>
            <Input
              id="auto-doc-path"
              value={path}
              onChange={(event) => setPath(event.target.value)}
              placeholder="architecture/overview"
            />
            <p className="text-[11px] text-muted-foreground">
              Supports folders. We'll save it as a markdown file.
            </p>
          </div>
          <AlertDialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={!path.trim()}>
              Publish
            </Button>
          </AlertDialogFooter>
        </form>
      </AlertDialogContent>
    </AlertDialog>
  );
}
