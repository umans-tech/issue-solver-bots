import { useSession } from 'next-auth/react';
import { PlusIcon, UserIcon, PenIcon, ChevronDownIcon } from '@/components/icons';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { getInitials, generatePastelColor } from '@/lib/utils';

interface SpaceSelectorProps {
  spaceName: string;
  spaceId: string;
  onCreateSpace?: () => void;
  onInviteToSpace?: () => void;
  onRenameSpace?: (newName: string) => void;
  onSwitchSpace?: (spaceId: string) => void;
}

export function SpaceSelector({ 
  spaceName,
  spaceId,
  onCreateSpace,
  onInviteToSpace,
  onRenameSpace,
  onSwitchSpace
}: SpaceSelectorProps) {
  const { data: session } = useSession();
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
            <ChevronDownIcon size={16} />
          </div>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-60">
        <DropdownMenuItem onClick={onCreateSpace}>
          <div className="mr-2">
            <PlusIcon size={16} />
          </div>
          <span>Create New Space</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        {session?.user?.spaces?.map((space) => (
          <DropdownMenuItem
            key={space.id}
            onClick={() => onSwitchSpace?.(space.id)}
            className={space.id === spaceId ? 'bg-muted' : ''}
          >
            <div className="w-6 h-6 rounded-lg flex items-center justify-center text-xs font-semibold text-white mr-2"
              style={{ backgroundImage: generatePastelColor(space.name) }}>
              {getInitials(space.name)}
            </div>
            <span>{space.name}</span>
          </DropdownMenuItem>
        ))}
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={onInviteToSpace}>
          <div className="mr-2">
            <UserIcon size={16} />
          </div>
          <span>Invite to Space</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => onRenameSpace?.(spaceName)}>
          <div className="mr-2">
            <PenIcon size={16} />
          </div>
          <span>Rename Space</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}