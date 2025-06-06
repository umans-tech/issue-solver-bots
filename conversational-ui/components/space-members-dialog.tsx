import { useState, useEffect } from 'react';
import { Users, Mail, CheckCircle, Clock } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { Avatar } from '@/components/ui/avatar';

interface SpaceMember {
  id: string;
  email: string;
  emailVerified: Date | null;
}

interface SpaceMembersResponse {
  members: SpaceMember[];
  currentUserId: string;
}

interface SpaceMembersDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  spaceId: string;
  spaceName: string;
}

export function SpaceMembersDialog({
  open,
  onOpenChange,
  spaceId,
  spaceName,
}: SpaceMembersDialogProps) {
  const [members, setMembers] = useState<SpaceMember[]>([]);
  const [currentUserId, setCurrentUserId] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open && spaceId) {
      fetchMembers();
    }
  }, [open, spaceId]);

  const fetchMembers = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/spaces/${spaceId}/members`);

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to fetch members');
      }

      const data: SpaceMembersResponse = await response.json();
      setMembers(data.members);
      setCurrentUserId(data.currentUserId);
    } catch (error) {
      console.error('Error fetching members:', error);
      setError(error instanceof Error ? error.message : 'Failed to fetch members');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent>
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            {spaceName} Members
          </SheetTitle>
          <SheetDescription>
            View all members who have access to this space.
          </SheetDescription>
        </SheetHeader>

        <div className="py-6">
          {isLoading && (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          )}

          {error && (
            <div className="text-center py-8">
              <p className="text-sm text-red-500">{error}</p>
            </div>
          )}

          {!isLoading && !error && members.length === 0 && (
            <div className="text-center py-8">
              <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-sm text-muted-foreground">No members found</p>
            </div>
          )}

          {!isLoading && !error && members.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  {members.length} {members.length === 1 ? 'member' : 'members'}
                </p>
              </div>

              <div className="space-y-3">
                {members.map((member) => (
                  <div
                    key={member.id}
                    className="flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-muted/50 transition-colors"
                  >
                    <div className="relative">
                      <Avatar
                          user={{ email: member.email }}
                          size={40}
                      />
                      {member.id === currentUserId && (
                        <Badge
                          variant="secondary"
                          className="absolute -top-1 -right-1 text-xs px-1 py-0 h-5 text-[10px] font-medium"
                        >
                          Me
                        </Badge>
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <Mail className="h-4 w-4 text-muted-foreground" />
                        <span className="text-sm font-medium truncate">
                          {member.email}
                        </span>
                      </div>

                      <div className="flex items-center gap-2 mt-1">
                        {member.emailVerified ? (
                          <Badge variant="secondary" className="text-xs">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Verified
                          </Badge>
                        ) : (
                          <Badge variant="outline" className="text-xs">
                            <Clock className="h-3 w-3 mr-1" />
                            Pending
                          </Badge>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
} 