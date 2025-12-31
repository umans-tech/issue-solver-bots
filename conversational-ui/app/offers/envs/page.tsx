'use client';

import Link from 'next/link';
import { IconUmansLogo } from '@/components/icons';
import { Button, buttonVariants } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { EnvsWaitlistForm } from '@/components/envs-waitlist-form';
import { Check, Terminal, Zap, Shield, GitBranch, RefreshCw, Box } from 'lucide-react';
import { useEffect, useState } from 'react';
import type { MouseEventHandler } from 'react';
import { usePostHog } from 'posthog-js/react';
import { FaDiscord, FaLinkedinIn, FaXTwitter } from 'react-icons/fa6';
import { ThemeToggle } from '@/components/theme-toggle';
import { cn } from '@/lib/utils';

function DemoTerminal() {
  const [lines, setLines] = useState<string[]>([]);
  
  useEffect(() => {
    const sequence = [
      { text: '> envs.create_sandbox(profile="my-repo")', delay: 500 },
      { text: 'Connected (2.1s)', delay: 1500, color: 'text-green-500' },
      { text: '> Running tests...', delay: 2500 },
      { text: '✓ Tests passed', delay: 4000, color: 'text-green-500' },
      { text: 'Snapshot created: snap-8f2a9c', delay: 4500, color: 'text-blue-500' },
      { text: '> Forking sandbox for parallel exec...', delay: 5500 },
      { text: 'Ready.', delay: 6500 },
    ];

    let timeouts: NodeJS.Timeout[] = [];
    
    // Reset and start
    setLines([]);
    
    sequence.forEach((item) => {
      const t = setTimeout(() => {
        setLines(prev => [...prev, `<span class="${item.color || ''}">${item.text}</span>`]);
      }, item.delay);
      timeouts.push(t);
    });

    return () => timeouts.forEach(clearTimeout);
  }, []);

  return (
    <div className="bg-zinc-950 rounded-lg border border-zinc-800 p-4 font-mono text-sm text-zinc-300 shadow-2xl w-full max-w-2xl mx-auto h-[240px] flex flex-col relative z-20">
      <div className="flex gap-1.5 mb-4">
        <div className="w-3 h-3 rounded-full bg-red-500/20"></div>
        <div className="w-3 h-3 rounded-full bg-yellow-500/20"></div>
        <div className="w-3 h-3 rounded-full bg-green-500/20"></div>
      </div>
      <div className="space-y-2 flex-1 overflow-hidden">
        {lines.map((line, i) => (
          <div key={i} dangerouslySetInnerHTML={{ __html: line }} />
        ))}
        <div className="animate-pulse inline-block w-2 h-4 bg-zinc-500 align-middle"></div>
      </div>
    </div>
  );
}

export default function EnvsPage() {
  const posthog = usePostHog();
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const [isScrolled, setIsScrolled] = useState(false);
  const earlyAccessHref = 'mailto:contact@umans.ai?subject=Early%20Access%20Request%20for%20Envs';

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: e.clientX / window.innerWidth,
        y: e.clientY / window.innerHeight,
      });
    };

    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('scroll', handleScroll);
    return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  useEffect(() => {
    // Observer for pricing view
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            posthog?.capture('view_pricing', { waitlist_id: 'envs', page_path: '/offers/envs' });
            observer.disconnect();
          }
        });
      },
      { threshold: 0.5 }
    );

    const pricingSection = document.getElementById('pricing');
    if (pricingSection) observer.observe(pricingSection);

    return () => observer.disconnect();
  }, [posthog]);

  const scrollToWaitlist = () => {
    document.getElementById('waitlist')?.scrollIntoView({ behavior: 'smooth' });
    posthog?.capture('click_join_waitlist', { location: 'hero' });
  };

  const handleEarlyAccessClick: MouseEventHandler<HTMLAnchorElement> = (event) => {
    posthog?.capture('click_request_early_access');
    // Ensure the mail client opens even if other handlers interfere with default navigation.
    event.preventDefault();
    window.location.assign(earlyAccessHref);
  };

  return (
    <div className="relative min-h-screen bg-background text-foreground font-sans selection:bg-primary/20 overflow-hidden">
      
       {/* Dynamic gradient background */}
       <div
        className="absolute inset-0 transition-opacity duration-500"
        style={{
          background: `radial-gradient(circle at ${mousePosition.x * 100}% ${mousePosition.y * 100}%, 
            rgba(99, 102, 241, 0.25) 0%, 
            rgba(147, 51, 234, 0.15) 35%,
            rgba(99, 102, 241, 0) 70%)`,
        }}
      />

      {/* Additional background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Floating orbs */}
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-gradient-to-br from-purple-500/10 to-blue-500/10 rounded-full blur-3xl animate-pulse" />
        <div
          className="absolute top-3/4 right-1/4 w-96 h-96 bg-gradient-to-br from-blue-500/8 to-indigo-500/8 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: '2s' }}
        />
        <div
          className="absolute top-1/2 left-3/4 w-48 h-48 bg-gradient-to-br from-violet-500/12 to-purple-500/12 rounded-full blur-3xl animate-pulse"
          style={{ animationDelay: '4s' }}
        />

        {/* Subtle grid pattern */}
        <div className="absolute inset-0 bg-grid-pattern opacity-5 dark:opacity-10" />
      </div>

      {/* Nav */}
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
            isScrolled
            ? 'bg-background/80 backdrop-blur-lg border-b border-border/50'
            : 'bg-transparent'
        }`}
      >
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
                {/* Left: Logo + Links */}
                <div className="flex items-center gap-10">
                    <Link href="/" className="flex items-center gap-2">
                        <IconUmansLogo className="h-8 w-auto" />
                        <span className="font-medium text-lg tracking-tight">envs</span>
                    </Link>
                    <div className="hidden md:flex items-center gap-6 text-sm">
                        <Link
                            href="https://blog.umans.ai"
                            className="text-foreground/80 hover:text-foreground transition-colors"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            Blog
                        </Link>
                         <a
                            href="https://discord.gg/Q5hdNrk7Rw"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-foreground/80 hover:text-foreground transition-colors"
                        >
                            Community
                        </a>
                    </div>
                </div>

                {/* Right: Socials + Theme + CTA */}
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
                    
                    <ThemeToggle variant="ghost" />
                    
                    <Button size="sm" onClick={scrollToWaitlist}>Join Waitlist</Button>
                </div>
            </div>
        </div>
      </nav>

      <main className="relative z-10">
        {/* 1. Hero */}
        <section className="pt-32 pb-20 lg:pt-40 lg:pb-32 px-6 text-center max-w-5xl mx-auto">
          {/* A/B Test Variants:
              1. "Repo-ready sandboxes for AI agents. MCP-native." (Original)
              2. "The infrastructure for autonomous software engineering."
              3. "Give your AI agents a real developer environment."
          */}
          <h1 className="text-5xl sm:text-7xl font-bold tracking-tight mb-8 text-foreground text-balance">
            <span className="bg-gradient-to-r from-indigo-500 to-purple-600 bg-clip-text text-transparent">
              Repo-ready sandboxes
            </span>
            <br className="hidden md:block" />
            <span className="block md:inline mt-2 md:mt-0"> for AI agents.</span>
            <br className="hidden md:block" />
            <span className="bg-gradient-to-r from-indigo-500 to-purple-600 bg-clip-text text-transparent block md:inline mt-2 md:mt-0">
              MCP-native.
            </span>
          </h1>
          <p className="text-xl text-muted-foreground mb-12 max-w-2xl mx-auto leading-relaxed">
            Deterministic dev environments that spin up in seconds. 
            Stream command output to your agents, snapshot state, and fork instantly.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
            <Button size="lg" className="h-12 px-8 text-base" onClick={scrollToWaitlist}>
              Join the waitlist
            </Button>
            <a
              href={earlyAccessHref}
              onClick={handleEarlyAccessClick}
              className={cn(buttonVariants({ variant: 'outline', size: 'lg' }), "h-12 px-8 text-base")}
            >
              Request early access
            </a>
          </div>
          
          <p className="text-sm text-muted-foreground/60">
            Built from the infrastructure we use at Umans to run remote coding agents on real repos.
          </p>
        </section>

        {/* 2. Proof Visual */}
        <section className="px-6 pb-32">
          <DemoTerminal />
        </section>

        {/* 3. Problem */}
        <section className="py-24">
          <div className="max-w-4xl mx-auto px-6">
             <div className="grid md:grid-cols-3 gap-8 text-center md:text-left">
                <div>
                   <div className="mb-4 inline-flex items-center justify-center w-10 h-10 rounded-lg bg-red-500/10 text-red-500">
                      <Zap size={20} />
                   </div>
                   <h3 className="font-semibold text-lg mb-2">Setup kills agents</h3>
                   <p className="text-muted-foreground">Agents fail when environments are flaky. Configuring dependencies and toolchains per-run is slow and error-prone.</p>
                </div>
                <div>
                   <div className="mb-4 inline-flex items-center justify-center w-10 h-10 rounded-lg bg-orange-500/10 text-orange-500">
                      <Terminal size={20} />
                   </div>
                   <h3 className="font-semibold text-lg mb-2">"Code exec" isn't enough</h3>
                   <p className="text-muted-foreground">Simple code sandboxes lack the services (Redis, PG) and full repo context needed for real engineering work.</p>
                </div>
                 <div>
                   <div className="mb-4 inline-flex items-center justify-center w-10 h-10 rounded-lg bg-blue-500/10 text-blue-500">
                      <RefreshCw size={20} />
                   </div>
                   <h3 className="font-semibold text-lg mb-2">State matters</h3>
                   <p className="text-muted-foreground">Multi-step tasks need reproducibility. You need to snapshot state, fork it, and roll back when agents mess up.</p>
                </div>
             </div>
          </div>
        </section>

        {/* 4. What you get */}
        <section className="py-24 max-w-5xl mx-auto px-6">
          <h2 className="text-3xl font-bold text-center mb-16">Infrastructure for autonomous coding</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="bg-card/40 backdrop-blur-sm border-border/50">
              <CardHeader>
                <GitBranch className="w-8 h-8 mb-2 text-primary" />
                <CardTitle>Repo Profiles</CardTitle>
                <CardDescription>Pre-configured environments.</CardDescription>
              </CardHeader>
              <CardContent>
                Define deps, services, and toolchains once. We build and cache images so sandboxes start instantly.
              </CardContent>
            </Card>

            <Card className="bg-card/40 backdrop-blur-sm border-border/50">
               <CardHeader>
                <RefreshCw className="w-8 h-8 mb-2 text-primary" />
                <CardTitle>Snapshots & Forks</CardTitle>
                <CardDescription>Time travel for agents.</CardDescription>
              </CardHeader>
              <CardContent>
                Snapshot a running sandbox, then fork it 10 times to let agents explore different solutions in parallel.
              </CardContent>
            </Card>

             <Card className="bg-card/40 backdrop-blur-sm border-border/50">
               <CardHeader>
                <Terminal className="w-8 h-8 mb-2 text-primary" />
                <CardTitle>Streaming Exec</CardTitle>
                <CardDescription>Real-time feedback.</CardDescription>
              </CardHeader>
              <CardContent>
                Don't wait for command completion. Stream stdout/stderr back to the agent for immediate reaction.
              </CardContent>
            </Card>

             <Card className="bg-card/40 backdrop-blur-sm border-border/50">
               <CardHeader>
                <Box className="w-8 h-8 mb-2 text-primary" />
                <CardTitle>MCP-Native</CardTitle>
                <CardDescription>Plug and play.</CardDescription>
              </CardHeader>
              <CardContent>
                Connects via Model Context Protocol. Use our standard MCP server to give any agent control over the sandbox.
              </CardContent>
            </Card>

             <Card className="bg-card/40 backdrop-blur-sm border-border/50">
               <CardHeader>
                <Shield className="w-8 h-8 mb-2 text-primary" />
                <CardTitle>Enterprise Controls</CardTitle>
                <CardDescription>Safe by default.</CardDescription>
              </CardHeader>
              <CardContent>
                Define egress rules, inject secrets securely, and audit every command executed by the agent.
              </CardContent>
            </Card>
          </div>
        </section>

        {/* 5. How it works */}
        <section className="py-20">
           <div className="max-w-4xl mx-auto px-6 text-center">
              <h2 className="text-3xl font-bold mb-12">How it works</h2>
              <div className="flex flex-col md:flex-row items-center justify-center gap-8 md:gap-4 relative">
                 {/* Steps */}
                 <div className="flex-1">
                    <div className="bg-card/40 backdrop-blur-sm border border-border/50 rounded-lg p-6 shadow-sm">
                       <div className="font-bold text-lg mb-2">1. Connect Repo</div>
                       <p className="text-sm text-muted-foreground">Link your GitHub repo and define a `devcontainer.json` or Dockerfile.</p>
                    </div>
                 </div>
                 <div className="hidden md:block text-muted-foreground">→</div>
                 <div className="flex-1">
                     <div className="bg-card/40 backdrop-blur-sm border border-border/50 rounded-lg p-6 shadow-sm">
                       <div className="font-bold text-lg mb-2">2. Start Sandbox</div>
                       <p className="text-sm text-muted-foreground">Agent requests a fresh environment. We boot it from warm cache.</p>
                    </div>
                 </div>
                 <div className="hidden md:block text-muted-foreground">→</div>
                 <div className="flex-1">
                     <div className="bg-card/40 backdrop-blur-sm border border-border/50 rounded-lg p-6 shadow-sm">
                       <div className="font-bold text-lg mb-2">3. Run Tasks</div>
                       <p className="text-sm text-muted-foreground">Agent executes tools via MCP. We stream output and track state.</p>
                    </div>
                 </div>
              </div>
           </div>
        </section>

        {/* 6. Differentiation */}
        <section className="py-24 max-w-4xl mx-auto px-6">
           <h2 className="text-3xl font-bold mb-8 text-center">Why not just use "code sandboxes"?</h2>
           <div className="bg-card/40 backdrop-blur-sm border border-border/50 rounded-xl p-8">
              <p className="text-lg leading-relaxed mb-6">
                 Generic "run untrusted code" APIs are built for snippet execution, not engineering. 
                 They lack the persistent filesystem, background services, and deterministic toolchain setup that real repos require.
              </p>
              <p className="text-lg leading-relaxed">
                 <strong>envs</strong> is built for <span className="text-primary font-medium">repository-scale work</span>. 
                 We handle the heavy lifting of building and caching your environment so your agent can focus on the code.
              </p>
           </div>
        </section>

        {/* 7. Pricing Smoke Test */}
        <section id="pricing" className="py-24 max-w-5xl mx-auto px-6">
           <h2 className="text-3xl font-bold mb-4 text-center">Pricing</h2>
           <p className="text-center text-muted-foreground mb-12">Waitlist members get early access.</p>
           
           <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
              <Card className="border-border/50 relative overflow-hidden bg-card/40 backdrop-blur-sm">
                 <div className="absolute top-0 left-0 w-full h-1 bg-muted-foreground/20"></div>
                 <CardHeader>
                    <CardTitle className="text-xl">Starter</CardTitle>
                    <div className="text-3xl font-bold mt-2">$29 <span className="text-sm font-normal text-muted-foreground">/ month</span></div>
                    <CardDescription>For individual developers</CardDescription>
                 </CardHeader>
                 <CardContent>
                    <ul className="space-y-3 text-sm">
                       <li className="flex items-center gap-2"><Check size={16} className="text-primary"/> 100 sandbox hours</li>
                       <li className="flex items-center gap-2"><Check size={16} className="text-primary"/> 2 concurrent sandboxes</li>
                       <li className="flex items-center gap-2"><Check size={16} className="text-primary"/> Standard machine types</li>
                    </ul>
                 </CardContent>
              </Card>

               <Card className="border-primary/20 relative overflow-hidden shadow-lg bg-primary/5 backdrop-blur-sm">
                 <div className="absolute top-0 left-0 w-full h-1 bg-primary"></div>
                 <Badge className="absolute top-4 right-4">Most Popular</Badge>
                 <CardHeader>
                    <CardTitle className="text-xl">Team</CardTitle>
                    <div className="text-3xl font-bold mt-2">$149 <span className="text-sm font-normal text-muted-foreground">/ month</span></div>
                    <CardDescription>For engineering teams</CardDescription>
                 </CardHeader>
                 <CardContent>
                    <ul className="space-y-3 text-sm">
                       <li className="flex items-center gap-2"><Check size={16} className="text-primary"/> 500 sandbox hours</li>
                       <li className="flex items-center gap-2"><Check size={16} className="text-primary"/> 10 concurrent sandboxes</li>
                       <li className="flex items-center gap-2"><Check size={16} className="text-primary"/> Powerful machine types</li>
                       <li className="flex items-center gap-2"><Check size={16} className="text-primary"/> Shared snapshots</li>
                    </ul>
                 </CardContent>
              </Card>
           </div>
           
           <div className="text-center mt-8 text-sm text-muted-foreground">
              <p>Enterprise / VPC needs? Talk to us.</p>
           </div>
        </section>

        {/* 8. Waitlist Form */}
        <section id="waitlist" className="py-24 border-t border-border/40">
           <div className="max-w-md mx-auto px-6 text-center">
              <h2 className="text-3xl font-bold mb-4">Join the waitlist</h2>
              <p className="text-muted-foreground mb-8">
                 We're onboarding teams gradually to ensure stability. 
                 Reserve your spot today.
              </p>
              <EnvsWaitlistForm />
           </div>
        </section>

        {/* 9. Coming Soon */}
        <section className="py-16 text-center">
           <div className="inline-block px-4 py-2 rounded-full bg-muted border border-border text-sm text-muted-foreground">
              <span className="font-semibold text-foreground">Coming soon:</span> Productivity sandboxes (Excel, PowerPoint) for agent-driven deliverables.
           </div>
        </section>

        {/* 10. FAQ */}
        <section className="py-20 max-w-3xl mx-auto px-6">
           <h2 className="text-2xl font-bold mb-10 text-center">Frequently Asked Questions</h2>
           <div className="space-y-6">
              <div>
                 <h3 className="font-semibold mb-2">Do you support devcontainer.json?</h3>
                 <p className="text-muted-foreground text-sm">Yes. We use standard devcontainers to build your environment image, so you can reuse your existing configuration.</p>
              </div>
               <div>
                 <h3 className="font-semibold mb-2">How fast do sandboxes start?</h3>
                 <p className="text-muted-foreground text-sm">Warm starts (from prebuilt image) take less than 2 seconds. Cold starts depend on your build time, but we cache aggressively.</p>
              </div>
               <div>
                 <h3 className="font-semibold mb-2">Can I run this in my own VPC?</h3>
                 <p className="text-muted-foreground text-sm">Yes, for enterprise plans. We can deploy the data plane in your AWS/GCP account while we manage the control plane.</p>
              </div>
               <div>
                 <h3 className="font-semibold mb-2">How do snapshots work?</h3>
                 <p className="text-muted-foreground text-sm">We use copy-on-write filesystems. Taking a snapshot is near-instant, and forking from a snapshot creates a new isolated environment sharing the base layer.</p>
              </div>
               <div>
                 <h3 className="font-semibold mb-2">Is there egress control?</h3>
                 <p className="text-muted-foreground text-sm">Yes. You can whitelist domains that agents are allowed to access. By default, we block everything except package registries.</p>
              </div>
           </div>
        </section>
        
        <footer className="py-12 border-t border-border/40 text-center text-sm text-muted-foreground bg-muted/20">
           <p>© {new Date().getFullYear()} Umans AI. All rights reserved.</p>
        </footer>
      </main>
    </div>
  );
}
