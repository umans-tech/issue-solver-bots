import { useState } from 'react';
import { useSession } from 'next-auth/react';
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

interface SpaceRenameDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  currentName: string;
  spaceId: string;
}

export function SpaceRenameDialog({
  open,
  onOpenChange,
  currentName,
  spaceId,
}: SpaceRenameDialogProps) {
  const { data: session, update: updateSession } = useSession();
  const [newName, setNewName] = useState(currentName);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || newName === currentName) {
      onOpenChange(false);
      return;
    }

    setIsLoading(true);
    try {
      const response = await fetch('/api/spaces/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          spaceId,
          name: newName.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to update space name');
      }

      const updatedSpace = await response.json();

      // Update the session with the new space data
      await updateSession({
        user: {
          ...session?.user,
          selectedSpace: {
            ...session?.user?.selectedSpace,
            name: newName.trim(),
          },
        },
      });

      onOpenChange(false);
    } catch (error) {
      console.error('Error updating space name:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent className="sm:max-w-[425px]">
        <AlertDialogHeader>
          <AlertDialogTitle>Rename Space</AlertDialogTitle>
        </AlertDialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Space Name</Label>
            <Input
              id="name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Enter space name"
              autoFocus
            />
          </div>
          <AlertDialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isLoading || !newName.trim() || newName === currentName}
            >
              {isLoading ? 'Saving...' : 'Save'}
            </Button>
          </AlertDialogFooter>
        </form>
      </AlertDialogContent>
    </AlertDialog>
  );
}
