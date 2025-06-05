import { Plus, UserPlus, Edit, ChevronDown, Users } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuGroup,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import { getInitials, generatePastelColor } from '@/lib/utils';

interface Space {
  id: string;
  name: string;
  knowledgeBaseId?: string | null;
  processId?: string | null;
  isDefault?: boolean;
}

interface SpaceSelectorProps {
  spaceName: string;
  spaceId: string;
  spaces: Space[];
  onCreateSpace?: () => void;
  onInviteToSpace?: () => void;
  onViewMembers?: () => void;
  onRenameSpace?: (newName: string) => void;
  onSwitchSpace?: (spaceId: string) => void;
}

export function SpaceSelector({ 
  spaceName,
  spaceId,
  spaces,
  onCreateSpace,
  onInviteToSpace,
  onViewMembers,
  onRenameSpace,
  onSwitchSpace
}: SpaceSelectorProps) {
  const initials = getInitials(spaceName || 'Default Space');
  const backgroundImage = generatePastelColor(spaceName);
  
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="flex items-center gap-2 px-2 hover:bg-muted rounded-md h-auto py-1 min-w-[200px]"
        >
          <div 
            className="w-8 h-8 flex-shrink-0 rounded-lg flex items-center justify-center text-sm font-semibold text-white shadow-sm ring-1 ring-white/10"
            style={{ 
              backgroundImage,
              boxShadow: '0 2px 4px rgba(0,0,0,0.05), inset 0 1px 2px rgba(255,255,255,0.15)'
            }}
          >
            {initials}
          </div>
          <span className="text-lg font-semibold truncate flex-1">{spaceName || 'Default Space'}</span>
          <div className="flex-shrink-0">
            <ChevronDown size={16} />
          </div>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-60">
        <DropdownMenuGroup>
          <DropdownMenuLabel>Your Spaces</DropdownMenuLabel>
          {spaces.map((space) => (
            <DropdownMenuItem
              key={space.id}
              onClick={() => onSwitchSpace?.(space.id)}
              className={`flex items-center ${space.id === spaceId ? 'bg-muted' : ''}`}
            >
              <div 
                className="w-6 h-6 rounded-lg flex items-center justify-center text-xs font-semibold text-white mr-2"
                style={{ backgroundImage: generatePastelColor(space.name) }}
              >
                {getInitials(space.name)}
              </div>
              <span className="flex-1 truncate">{space.name}</span>
              {space.id === spaceId && (
                <div className="w-2 h-2 rounded-full bg-primary ml-2" />
              )}
            </DropdownMenuItem>
          ))}
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuGroup>
          <DropdownMenuLabel>Manage Current Space</DropdownMenuLabel>
          <DropdownMenuItem onClick={onViewMembers}>
            <div className="mr-2">
              <Users size={16} />
            </div>
            <span>View Members</span>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={onInviteToSpace}>
            <div className="mr-2">
              <UserPlus size={16} />
            </div>
            <span>Invite to Space</span>
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => onRenameSpace?.(spaceName)}>
            <div className="mr-2">
              <Edit size={16} />
            </div>
            <span>Rename Space</span>
          </DropdownMenuItem>
        </DropdownMenuGroup>
        <DropdownMenuItem onClick={onCreateSpace}>
          <div className="mr-2">
            <Plus size={16} />
          </div>
          <span>Create New Space</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}