import { ChevronDownIcon, PlusIcon, UserPlusIcon } from 'lucide-react';
import { Button } from './ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from './ui/dropdown-menu';

function getInitials(name: string) {
  return name
    .split(' ')
    .map((word) => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
}

function generatePastelColor(text: string) {
  if (!text || text === 'Default Space') {
    // Dégradé par défaut plus visible et élégant
    return 'linear-gradient(135deg, #00DC82 0%, #36E4DA 100%)';
  }

  // Génère une couleur basée sur le texte pour les autres cas
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    hash = text.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  const h = hash % 360;
  // Augmentation de la saturation et ajustement de la luminosité pour plus de contraste
  const s = 85 + (hash % 15); // Variation de saturation entre 85-100%
  const l1 = 65 + (hash % 10); // Première couleur
  const l2 = 45 + (hash % 15); // Deuxième couleur plus foncée pour meilleur contraste
  
  return `linear-gradient(135deg, hsl(${h}, ${s}%, ${l1}%) 0%, hsl(${h}, ${s}%, ${l2}%) 100%)`;
}

export function SpaceSelector({ 
  spaceName,
  onCreateSpace,
  onInviteToSpace 
}: { 
  spaceName: string;
  onCreateSpace?: () => void;
  onInviteToSpace?: () => void;
}) {
  const initials = getInitials(spaceName || 'Default Space');
  const backgroundImage = generatePastelColor(spaceName);
  
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="flex items-center gap-2 px-2 hover:bg-muted rounded-md h-auto py-1"
        >
          <div 
            className="w-8 h-8 rounded-lg flex items-center justify-center text-sm font-semibold text-white shadow-sm ring-1 ring-white/10"
            style={{ 
              backgroundImage,
              boxShadow: '0 2px 4px rgba(0,0,0,0.05), inset 0 1px 2px rgba(255,255,255,0.15)'
            }}
          >
            {initials}
          </div>
          <span className="text-lg font-semibold">{spaceName || 'Default Space'}</span>
          <ChevronDownIcon className="h-4 w-4 text-muted-foreground" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-60">
        <DropdownMenuItem onClick={onCreateSpace}>
          <PlusIcon className="mr-2 h-4 w-4" />
          <span>Create New Space</span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={onInviteToSpace}>
          <UserPlusIcon className="mr-2 h-4 w-4" />
          <span>Invite to Space</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}