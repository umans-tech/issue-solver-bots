'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { SidebarToggle } from '@/components/sidebar-toggle';
import { Button } from '@/components/ui/button';
import { GitIcon } from './icons';
import { useSidebar } from './ui/sidebar';
import { ThemeToggle } from './theme-toggle';
import { IconUmansLogo } from './icons';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';

export function TaskHeader() {
  const router = useRouter();
  const { open } = useSidebar();

  return (
    <header className="sticky top-0 z-50 flex items-center justify-between w-full h-16 px-4 border-b shrink-0 bg-background">
      <div className="flex items-center">
        <SidebarToggle />
      </div>

      <div className="flex items-center gap-2 md:flex py-1.5 px-2 h-fit md:h-[34px] order-4 md:ml-auto">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={() => router.push('/')}
            >
              <GitIcon />
              <span className="sr-only">Go to Home</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent>Go to Home</TooltipContent>
        </Tooltip>
        <ThemeToggle />
        <Link href="/landing">
          <IconUmansLogo className="h-16 w-16" />
        </Link>
      </div>
    </header>
  );
} 