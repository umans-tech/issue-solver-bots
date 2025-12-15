'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { IconUmansLogo } from '@/components/icons';
import { ThemeToggle } from '@/components/theme-toggle';
import { Button } from '@/components/ui/button';
import { FaDiscord, FaLinkedinIn, FaXTwitter } from 'react-icons/fa6';

export function LandingNavbar() {
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // Keep it simple: use the same flow as "Start Building" by linking to
  // `/go-to-app`, which reliably hands off to the correct domain.

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-background/80 backdrop-blur-lg border-b border-border/50'
          : 'bg-transparent'
      }`}
    >
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left area: logo + primary nav */}
          <div className="flex items-center gap-10">
            <Link href="/" className="flex items-center">
              <IconUmansLogo className="h-8 w-auto" />
            </Link>
            <nav className="landing-nav hidden md:flex items-center gap-6 text-sm">
              <Link
                href="https://blog.umans.ai"
                className="text-foreground/80 hover:text-foreground transition-colors bg-transparent focus-visible:outline-none focus-visible:ring-0 px-0 py-0"
                target="_blank"
                rel="noopener noreferrer"
              >
                Blog
              </Link>
              <a
                href="https://discord.gg/Q5hdNrk7Rw"
                target="_blank"
                rel="noopener noreferrer"
                className="text-foreground/80 hover:text-foreground transition-colors bg-transparent focus-visible:outline-none focus-visible:ring-0 px-0 py-0"
              >
                Community
              </a>
              <Link
                href="#pricing"
                className="text-foreground/80 hover:text-foreground transition-colors bg-transparent focus-visible:outline-none focus-visible:ring-0 px-0 py-0"
              >
                Pricing
              </Link>
            </nav>
          </div>

          {/* Right side actions */}
          <div className="flex items-center space-x-4">
            <div className="hidden sm:flex items-center gap-3 text-foreground/80">
              <a
                href="https://discord.gg/Q5hdNrk7Rw"
                target="_blank"
                rel="noreferrer"
                className="hover:text-foreground"
              >
                <FaDiscord className="h-4 w-4" />
              </a>
              <a
                href="https://x.com/umans_ai"
                target="_blank"
                rel="noreferrer"
                className="hover:text-foreground"
              >
                <FaXTwitter className="h-4 w-4" />
              </a>
              <a
                href="https://www.linkedin.com/company/umans-ai"
                target="_blank"
                rel="noreferrer"
                className="hover:text-foreground"
              >
                <FaLinkedinIn className="h-4 w-4" />
              </a>
            </div>
            {/* Theme Toggle */}
            <ThemeToggle variant="ghost" />

            {/* Sign In Button */}
            <Link href="/go-to-app">
              <Button variant="ghost" size="sm" className="text-sm font-medium">
                Sign In
              </Button>
            </Link>

            {/* Sign Up Button */}
            <Link href="/go-to-app">
              <Button size="sm" className="text-sm font-medium">
                Sign Up
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
