'use client';
import { ChevronUp } from 'lucide-react';
import type { User } from 'next-auth';
import { signOut } from 'next-auth/react';
import { useTheme } from 'next-themes';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useSession } from 'next-auth/react';
import { ManageBillingDialog } from '@/components/manage-billing-dialog';

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';
import { Avatar } from '@/components/ui/avatar';

export function SidebarUserNav({ user }: { user: User }) {
  const { setTheme, theme } = useTheme();
  const router = useRouter();
  const { data: session } = useSession();
  const plan = (session?.user as any)?.plan || 'free';

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton className="data-[state=open]:bg-sidebar-accent bg-background data-[state=open]:text-sidebar-accent-foreground h-10">
              <Avatar
                user={{
                  image: user.image,
                  name: user.name,
                  email: user.email
                }}
                size={24}
              />
              <span className="truncate">{user?.email}</span>
              <ChevronUp className="ml-auto" />
            </SidebarMenuButton>
          </DropdownMenuTrigger>
            <DropdownMenuContent
            side="top"
            className="w-[--radix-popper-anchor-width]"
          >
            <div className="px-2.5 py-2 text-xs text-muted-foreground flex items-center justify-between">
              <span>Plan</span>
              <span className={`rounded-full px-2 py-0.5 text-[10px] font-medium border ${plan === 'free' ? 'bg-muted text-foreground' : 'bg-emerald-600/10 text-emerald-700 dark:text-emerald-300 border-emerald-600/20'}`}>{plan}</span>
            </div>
            <DropdownMenuItem asChild>
              <div className="w-full">
                {plan === 'free' ? (
                  <button
                    type="button"
                    className="w-full text-left font-medium"
                    onClick={(e) => {
                      e.stopPropagation();
                      // Open pricing dialog programmatically to avoid nested trigger closing
                      window.dispatchEvent(new Event('open-pricing-dialog'));
                    }}
                  >
                    Upgrade plan
                  </button>
                ) : (
                  <button
                    type="button"
                    className="w-full text-left font-medium"
                    onClick={(e) => {
                      e.stopPropagation();
                      window.dispatchEvent(new Event('open-manage-billing'));
                    }}
                  >
                    Manage billing
                  </button>
                )}
              </div>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="cursor-pointer"
              onSelect={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            >
              {`Toggle ${theme === 'light' ? 'dark' : 'light'} mode`}
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/terms" className="cursor-pointer" target="_blank" rel="noopener noreferrer">
                Terms of Use
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/privacy" className="cursor-pointer" target="_blank" rel="noopener noreferrer">
                Privacy Policy
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <button
                type="button"
                className="w-full cursor-pointer"
                onClick={async () => {
                  try {
                    await signOut({
                      callbackUrl: '/',
                      redirect: true
                    });
                    // Force a page refresh to ensure the session is cleared
                    router.push('/login');
                    router.refresh();
                  } catch (error) {
                    console.error('Failed to sign out:', error);
                  }
                }}
              >
                Sign out
              </button>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        <ManageBillingDialog />
      </SidebarMenuItem>
    </SidebarMenu>
  );
}
