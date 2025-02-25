'use client';

import * as React from 'react';
import { useTheme } from 'next-themes';

import { Button } from '@/components/ui/button';
import { IconMoon, IconSun } from '@/components/icons';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';

export const ThemeToggle = ({
  variant = "ghost"
}: {
  variant?: React.ComponentProps<typeof Button>["variant"]
}) => {
  const { setTheme, theme } = useTheme();
  const [mounted, setMounted] = React.useState(false);
  const [_, startTransition] = React.useTransition();

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant={variant} size="icon">
            <IconSun className="transition-all" />
            <span className="sr-only">Toggle theme</span>
          </Button>
        </TooltipTrigger>
        <TooltipContent>{`Toggle ${theme === 'light' ? 'dark' : 'light'} mode`}</TooltipContent>
      </Tooltip>
    );
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          variant={variant}
          size="icon"
          onClick={() => {
            startTransition(() => {
              setTheme(theme === 'light' ? 'dark' : 'light');
            });
          }}
        >
          {theme === 'dark' ? (
            <IconMoon className="transition-all" />
          ) : (
            <IconSun className="transition-all" />
          )}
          <span className="sr-only">Toggle theme</span>
        </Button>
      </TooltipTrigger>
      <TooltipContent>{`Toggle ${theme === 'light' ? 'dark' : 'light'} mode`}</TooltipContent>
    </Tooltip>
  );
};
