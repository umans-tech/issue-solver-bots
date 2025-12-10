'use client';

import Link from 'next/link';
import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { LandingNavbar } from '@/components/landing-navbar';
import { 
  Brain, 
  Users,
  Bot, 
  FileText,
  Check, 
  Terminal, 
  Code, 
  GitBranch, 
  Layout, 
  Globe, 
  Shield, 
  MessageCircle 
} from 'lucide-react';
import { IconUmansLogo } from '@/components/icons';

export default function LandingPage() {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const featuresRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: e.clientX / window.innerWidth,
        y: e.clientY / window.innerHeight,
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');
  const [checkoutLoading, setCheckoutLoading] = useState<null | 'solo' | 'pro'>(null);

  const startCheckout = async (planKey: 'solo' | 'pro') => {
    try {
      setCheckoutLoading(planKey);
      const res = await fetch('/api/billing/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ plan: planKey, cycle: billingCycle }),
      });
      if (res.status === 401) {
        const payload = encodeURIComponent(JSON.stringify({ plan: planKey, cycle: billingCycle }));
        document.cookie = `pending_checkout=${payload}; Path=/; Max-Age=3600; SameSite=Lax`;
        window.location.href = `/register?plan=${planKey}&cycle=${billingCycle}`;
        return;
      }
      const data = await res.json();
      if (data?.url) {
        window.location.href = data.url as string;
      }
    } catch (e) {
      console.error('Failed to start checkout', e);
      setCheckoutLoading(null);
    }
  };

  const pricingPlans = [
    {
      name: 'Free',
      tagline: 'Great for exploring Umans',
      description: 'Spin up our browser-based coding agents and see how far the platform takes you.',
      features: [
        '15 daily agent credits (up to 50 monthly)',
        'GPT-5, Claude Sonnet & Claude Code in-browser sessions',
        'Auto-generated docs & diagrams for a personal space',
      ],
      ctaLabel: 'Start for free',
      ctaHref: '/go-to-app',
      ctaType: 'internal',
      ctaVariant: 'primary',
      popular: false,
      pricing: {
        monthly: { amount: '$0', descriptor: 'per user / month' },
        yearly: { amount: '$0', descriptor: 'per user / month' },
      },
    },
    {
      name: 'Solo',
      tagline: 'For solo founders and indie hackers',
      description: 'Level up with more credits and access to our newest GPT-5 powered workflows.',
      features: [
        '200 monthly agent credits',
        'Extended runs with GPT-5, Claude Sonnet & Claude Code',
        'Personal workspace with persistent context & docs',
      ],
      ctaLabel: 'Upgrade your team',
      ctaHref: 'https://buy.stripe.com/solo-plan-link',
      ctaType: 'external',
      ctaVariant: 'secondary',
      popular: false,
      pricing: {
        monthly: { amount: '$24', descriptor: 'per user / month' },
        yearly: { amount: '$19', descriptor: 'per user / month' },
      },
    },
    {
      name: 'Pro',
      tagline: 'Built for product teams that ship together',
      description: 'Share context across teammates and keep everyone aligned with living docs.',
      features: [
        '600 shared monthly agent credits',
        'Shared spaces with cross-conversation memory',
        'Seats for up to 5 collaborators (per-user pricing)',
      ],
      ctaLabel: 'Upgrade your team',
      ctaHref: 'https://buy.stripe.com/pro-plan-link',
      ctaType: 'external',
      ctaVariant: 'primary',
      popular: true,
      pricing: {
        monthly: { amount: '$49', descriptor: 'per user / month' },
        yearly: { amount: '$41', descriptor: 'per user / month' },
      },
    },
    {
      name: 'Enterprise',
      tagline: 'Tailored to your engineering org',
      description: 'Custom rollouts with deeper controls, security, and agent guardrails.',
      features: [
        'Custom credit pools & scaling guarantees',
        'Dedicated environment profiles per team',
        'White-glove enablement + shared roadmap planning',
      ],
      ctaLabel: 'Contact us for enterprise',
      ctaHref: 'mailto:contact@umans.ai',
      ctaType: 'external',
      ctaVariant: 'secondary',
      popular: false,
      pricing: {
        monthly: { amount: 'Flexible billing', descriptor: '' },
        yearly: { amount: 'Flexible billing', descriptor: '' },
      },
    },
  ] as const;

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Navigation Bar */}
      <LandingNavbar />

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
      
      {/* Additional background elements for visual interest */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Floating orbs */}
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-gradient-to-br from-purple-500/10 to-blue-500/10 rounded-full blur-3xl animate-pulse" />
        <div className="absolute top-3/4 right-1/4 w-96 h-96 bg-gradient-to-br from-blue-500/8 to-indigo-500/8 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-3/4 w-48 h-48 bg-gradient-to-br from-violet-500/12 to-purple-500/12 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '4s' }} />
        
        {/* Subtle grid pattern */}
        <div className="absolute inset-0 bg-grid-pattern opacity-5 dark:opacity-10" />
      </div>

      {/* Hero Section */}
      <section className="relative z-10 flex min-h-screen flex-col items-center justify-center p-4 pt-20 lg:pt-32">
        <div className="container mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-left"
          >
            <div className="inline-flex items-center px-3 py-1 rounded-full bg-secondary/50 text-secondary-foreground text-sm font-medium mb-6 backdrop-blur-sm border border-border/50">
              Deliver value, not just code.
            </div>
            
            <h1 className="mb-6 text-5xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-foreground to-foreground/70 sm:text-6xl text-balance">
              Delegate real coding work to AI agents, <br />
              from your browser.
            </h1>
            
            <h2 className="text-3xl font-bold mb-6">
              <span className="bg-gradient-to-r from-indigo-500 to-purple-600 bg-clip-text text-transparent">Not Only Code</span>
            </h2>

            <p className="mb-8 text-xl text-muted-foreground text-balance leading-relaxed">
              Connect Umans to your repo to chat with large codebases, delegate coding tasks to secure remote agents that ship PRs, and keep docs and diagrams in sync with reality. Bridge the gap between what your system does, what business needs, and what your team plans to build.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 mb-8">
              <Link
                href="/go-to-app"
                className="rounded-md bg-primary px-8 py-3 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary text-center"
              >
                Start for free
              </Link>
              <a
                href="mailto:contact@umans.ai"
                className="rounded-md bg-secondary/80 px-8 py-3 text-sm font-semibold text-secondary-foreground shadow-sm hover:bg-secondary focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-secondary text-center backdrop-blur-sm"
              >
                Talk to us about your team
              </a>
            </div>

            <ul className="space-y-2 text-sm text-muted-foreground">
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-500" />
                Chat with your codebase and generate architecture diagrams.
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-500" />
                Delegate coding tasks to agents that run tests and open PRs.
              </li>
              <li className="flex items-center gap-2">
                <Check className="w-4 h-4 text-green-500" />
                Generate living docs directly from your repo.
              </li>
            </ul>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative hidden lg:block"
          >
            {/* Fake Product UI Mockup */}
            <div className="rounded-xl border border-border bg-card/50 backdrop-blur shadow-2xl overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-border bg-muted/30">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-500/20" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/20" />
                  <div className="w-3 h-3 rounded-full bg-green-500/20" />
                </div>
                <div className="h-5 w-64 rounded-md bg-muted/50 ml-4" />
              </div>
              <div className="grid grid-cols-12 h-[500px]">
                {/* Chat Panel */}
                <div className="col-span-5 border-r border-border p-4 flex flex-col gap-4">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                      <Users className="w-4 h-4 text-primary" />
                    </div>
                    <div className="bg-muted/30 rounded-lg p-3 text-sm">
                      Can you refactor the payment validation logic?
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center shrink-0">
                      <Bot className="w-4 h-4 text-indigo-500" />
                    </div>
                    <div className="bg-indigo-500/5 border border-indigo-500/10 rounded-lg p-3 text-sm">
                      <p className="mb-2">I'll create an agent to handle this. It will:</p>
                      <ul className="list-disc pl-4 space-y-1 text-xs text-muted-foreground">
                        <li>Scan <code>payment_service.py</code></li>
                        <li>Run existing tests</li>
                        <li>Refactor validation methods</li>
                        <li>Open a PR</li>
                      </ul>
                      <div className="mt-3">
                         <span className="text-xs bg-indigo-500/20 text-indigo-600 dark:text-indigo-300 px-2 py-1 rounded">Agent Active</span>
                      </div>
                    </div>
                  </div>
                  <div className="mt-auto">
                    <div className="h-10 rounded-md bg-muted/30 border border-border" />
                  </div>
                </div>
                {/* PR/Code Panel */}
                <div className="col-span-7 bg-background p-6">
                  <div className="rounded-lg border border-border bg-card shadow-sm p-4 mb-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <GitBranch className="w-4 h-4 text-green-500" />
                        <span className="text-sm font-medium">PR #124: Refactor Payment Validation</span>
                      </div>
                      <span className="text-xs bg-green-500/10 text-green-600 px-2 py-0.5 rounded-full">Open</span>
                    </div>
                    <div className="space-y-2">
                       <div className="h-2 w-3/4 rounded bg-muted/50" />
                       <div className="h-2 w-1/2 rounded bg-muted/50" />
                    </div>
                  </div>
                  <div className="space-y-3 font-mono text-xs">
                    <div className="flex gap-2">
                       <span className="text-muted-foreground">1</span>
                       <span className="text-blue-500">class</span>
                       <span className="text-yellow-500">PaymentValidator</span>:
                    </div>
                    <div className="flex gap-2 pl-4">
                       <span className="text-muted-foreground">2</span>
                       <span className="text-blue-500">def</span>
                       <span className="text-yellow-500">validate_transaction</span>(self, tx):
                    </div>
                    <div className="flex gap-2 pl-8">
                       <span className="text-muted-foreground">3</span>
                       <span className="text-muted-foreground"># Validates transaction integrity</span>
                    </div>
                    <div className="flex gap-2 pl-8">
                       <span className="text-muted-foreground">4</span>
                       <span className="text-purple-500">if not</span> tx.is_valid():
                    </div>
                     <div className="flex gap-2 pl-12">
                       <span className="text-muted-foreground">5</span>
                       <span className="text-red-500">raise</span> ValidationError("Invalid tx")
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Why Teams Use Umans Section */}
      <section ref={featuresRef} className="relative z-10 bg-background py-24">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl font-bold text-foreground mb-4">Why teams use Umans</h2>
          </motion.div>

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
            {/* Card 1 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.1 }}
              viewport={{ once: true }}
              className="group landing-feature-card rounded-2xl bg-gradient-to-br from-card to-card/80 p-8 shadow-lg border border-border/50 hover:shadow-xl hover:border-border/80 transition-all duration-300 backdrop-blur-sm"
            >
              <div className="mb-4">
                <Brain className="w-8 h-8 text-primary group-hover:scale-110 transition-transform duration-300" />
              </div>
              <h3 className="text-xl font-bold text-foreground mb-4">Understand any codebase in hours, not weeks</h3>
              <p className="text-muted-foreground mb-6">
                Connect your repo and chat with an AI that actually navigates your code. Follow references, jump across services, and get diagrams, explanations, and root cause analyses instead of grep driven archaeology.
              </p>
              {/* Visual Hint */}
              <div className="rounded-lg bg-muted/30 border border-border/50 p-3 text-xs font-mono">
                <div className="flex items-center gap-2 mb-2">
                   <MessageCircle className="w-3 h-3" />
                   <span>"Explain the auth flow"</span>
                </div>
                <div className="pl-4 border-l-2 border-primary/30 text-muted-foreground">
                   Generating call graph...
                </div>
              </div>
            </motion.div>

            {/* Card 2 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              viewport={{ once: true }}
              className="group landing-feature-card rounded-2xl bg-gradient-to-br from-card to-card/80 p-8 shadow-lg border border-border/50 hover:shadow-xl hover:border-border/80 transition-all duration-300 backdrop-blur-sm"
            >
              <div className="mb-4">
                <Terminal className="w-8 h-8 text-primary group-hover:scale-110 transition-transform duration-300" />
              </div>
              <h3 className="text-xl font-bold text-foreground mb-4">Delegate coding work to secure remote agents</h3>
              <p className="text-muted-foreground mb-6">
                From the browser, delegate coding tasks to remote agents running in secure micro VMs. They use a real dev environment, run your tests, even open a browser when needed, and finish by sending a pull request.
              </p>
              {/* Visual Hint */}
               <div className="rounded-lg bg-black/80 border border-border/50 p-3 text-xs font-mono text-green-400">
                <div>$ run-tests ./billing</div>
                <div className="text-white/70">... 34 passed</div>
                <div className="mt-1">$ git push origin fix/billing</div>
                <div className="text-blue-400">Opening PR #123...</div>
              </div>
            </motion.div>

            {/* Card 3 */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              viewport={{ once: true }}
              className="group landing-feature-card rounded-2xl bg-gradient-to-br from-card to-card/80 p-8 shadow-lg border border-border/50 hover:shadow-xl hover:border-border/80 transition-all duration-300 backdrop-blur-sm"
            >
              <div className="mb-4">
                <FileText className="w-8 h-8 text-primary group-hover:scale-110 transition-transform duration-300" />
              </div>
              <h3 className="text-xl font-bold text-foreground mb-4">Keep architecture and docs close to reality</h3>
              <p className="text-muted-foreground mb-6">
                Define prompts once and let Umans generate system overviews, domain glossaries, and how tos from your code. Regenerate pages when things change so docs stay close to reality.
              </p>
              {/* Visual Hint */}
              <div className="rounded-lg bg-white dark:bg-slate-900 border border-border/50 p-3 text-xs">
                <div className="flex justify-between items-center mb-2 border-b border-border/30 pb-1">
                   <span className="font-semibold">System Architecture</span>
                   <span className="bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-1.5 py-0.5 rounded text-[10px]">Auto</span>
                </div>
                <div className="h-2 w-3/4 bg-muted mb-1 rounded"></div>
                <div className="h-2 w-1/2 bg-muted rounded"></div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Core Capabilities Section */}
      <section className="relative z-10 bg-muted/30 py-24">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
             <h2 className="text-3xl font-bold text-foreground mb-4">What you can do with Umans</h2>
          </motion.div>

          <div className="space-y-24">
            
            {/* Capability 1: Chat */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <MessageCircle className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="text-2xl font-bold">Chat with your codebase</h3>
                </div>
                <p className="text-lg text-muted-foreground mb-4">
                  Ask questions in natural language, get guided tours of complex flows, and quickly build mental models of large repositories.
                </p>
                <ul className="space-y-2 text-muted-foreground">
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-primary" /> Indexes large codebases reliably</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-primary" /> Generates diagrams and structured answers</li>
                </ul>
              </motion.div>
              <motion.div
                 initial={{ opacity: 0, x: 20 }}
                 whileInView={{ opacity: 1, x: 0 }}
                 transition={{ duration: 0.6 }}
                 viewport={{ once: true }}
                 className="rounded-xl border border-border bg-card/50 shadow-lg p-6 backdrop-blur-sm"
              >
                  {/* Fake Chat UI */}
                  <div className="space-y-4">
                     <div className="flex justify-end">
                        <div className="bg-primary text-primary-foreground rounded-2xl rounded-tr-sm px-4 py-2 text-sm max-w-[80%]">
                           How are notifications dispatched?
                        </div>
                     </div>
                     <div className="flex justify-start">
                        <div className="bg-muted rounded-2xl rounded-tl-sm px-4 py-2 text-sm max-w-[90%]">
                           <p className="mb-2">Notifications are handled by the <code>NotificationService</code> class. It uses a strategy pattern to dispatch via Email, SMS, or Push.</p>
                           <div className="bg-card border border-border rounded p-2 text-xs font-mono">
                              services/notification/dispatcher.py
                           </div>
                        </div>
                     </div>
                  </div>
              </motion.div>
            </div>

            {/* Capability 2: Agents */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
               <motion.div
                 initial={{ opacity: 0, x: -20 }}
                 whileInView={{ opacity: 1, x: 0 }}
                 transition={{ duration: 0.6 }}
                 viewport={{ once: true }}
                 className="order-2 lg:order-1 rounded-xl border border-border bg-card/50 shadow-lg p-6 backdrop-blur-sm relative overflow-hidden"
              >
                  {/* Fake Agent UI */}
                  <div className="absolute inset-0 bg-black/90 z-0"></div>
                  <div className="relative z-10 font-mono text-sm text-green-400 space-y-2">
                     <div>&gt; initialize_env --stack python-3.11</div>
                     <div className="text-white/60">Environment ready (2.1s)</div>
                     <div>&gt; run_test tests/api/test_orders.py</div>
                     <div className="text-red-400">FAIL: test_create_order_invalid_sku</div>
                     <div>&gt; read_file src/orders/service.py</div>
                     <div className="text-yellow-400">Analyzing failure...</div>
                     <div>&gt; apply_fix src/orders/service.py</div>
                     <div>&gt; run_test tests/api/test_orders.py</div>
                     <div className="text-green-400">PASS (0.4s)</div>
                     <div className="text-blue-400">Creating Pull Request...</div>
                  </div>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
                className="order-1 lg:order-2"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Bot className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="text-2xl font-bold">Coding agents on cloud micro VMs</h3>
                </div>
                <p className="text-lg text-muted-foreground mb-4">
                  Once a repo is connected, Umans prepares a micro VM snapshot with your stack. Agents share that snapshot, so it is like having a developer laptop ready from day one.
                </p>
                 <ul className="space-y-2 text-muted-foreground">
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-primary" /> Agents can run tests and terminal commands</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-primary" /> Capable of opening a browser in the VM</li>
                  <li className="flex items-center gap-2"><Check className="w-4 h-4 text-primary" /> Deliveries culminate in a Pull Request</li>
                </ul>
              </motion.div>
            </div>

            {/* Capability 3: Auto Docs */}
             <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
              >
                 <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <FileText className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="text-2xl font-bold">Auto docs</h3>
                </div>
                <p className="text-lg text-muted-foreground mb-4">
                  Use prompts to generate and regenerate pages like architecture overviews, domain event glossaries, or onboarding guides from your codebase.
                </p>
                <p className="text-muted-foreground">
                  Docs stay fresh because they are grounded in code and can be regenerated on demand, preventing wiki-rot.
                </p>
              </motion.div>
              <motion.div
                 initial={{ opacity: 0, x: 20 }}
                 whileInView={{ opacity: 1, x: 0 }}
                 transition={{ duration: 0.6 }}
                 viewport={{ once: true }}
                 className="rounded-xl border border-border bg-card/50 shadow-lg p-6 backdrop-blur-sm"
              >
                  {/* Fake Docs UI */}
                   <div className="flex gap-4">
                      <div className="w-1/4 space-y-2 border-r border-border pr-2">
                         <div className="h-2 w-3/4 bg-muted rounded"></div>
                         <div className="h-2 w-full bg-muted rounded"></div>
                         <div className="h-2 w-2/3 bg-muted rounded"></div>
                      </div>
                      <div className="w-3/4">
                         <div className="flex justify-between mb-4">
                            <div className="h-4 w-1/2 bg-foreground/20 rounded"></div>
                            <div className="px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 text-[10px] rounded">Live</div>
                         </div>
                         <div className="space-y-2">
                            <div className="h-2 w-full bg-muted rounded"></div>
                            <div className="h-2 w-full bg-muted rounded"></div>
                            <div className="h-2 w-3/4 bg-muted rounded"></div>
                            <div className="my-4 h-24 w-full bg-muted/50 border border-border border-dashed rounded flex items-center justify-center text-xs text-muted-foreground">
                               Generated Architecture Diagram
                            </div>
                         </div>
                      </div>
                   </div>
              </motion.div>
            </div>

            {/* Capability 4: Integrations */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
               <motion.div
                 initial={{ opacity: 0, x: -20 }}
                 whileInView={{ opacity: 1, x: 0 }}
                 transition={{ duration: 0.6 }}
                 viewport={{ once: true }}
                 className="order-2 lg:order-1 rounded-xl border border-border bg-card/50 shadow-lg p-8 backdrop-blur-sm flex items-center justify-center gap-8 flex-wrap"
              >
                  {/* Integration Logos/Badges */}
                  <div className="flex flex-col items-center gap-2">
                     <div className="w-12 h-12 bg-white rounded-lg shadow flex items-center justify-center">
                        <Globe className="w-6 h-6 text-black" />
                     </div>
                     <span className="text-xs font-medium">Notion</span>
                  </div>
                   <div className="flex flex-col items-center gap-2">
                     <div className="w-12 h-12 bg-black rounded-lg shadow flex items-center justify-center">
                        <GitBranch className="w-6 h-6 text-white" />
                     </div>
                     <span className="text-xs font-medium">GitHub</span>
                  </div>
                  <div className="flex flex-col items-center gap-2 opacity-50">
                     <div className="w-12 h-12 bg-blue-500 rounded-lg shadow flex items-center justify-center">
                        <MessageCircle className="w-6 h-6 text-white" />
                     </div>
                     <span className="text-xs font-medium">Slack (Soon)</span>
                  </div>
              </motion.div>
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6 }}
                viewport={{ once: true }}
                className="order-1 lg:order-2"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Globe className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="text-2xl font-bold">Integrations and spaces</h3>
                </div>
                <p className="text-lg text-muted-foreground mb-4">
                  Connect a repo to create a shared space for your team. Everyone gets access to the same chat context, docs, and coding agents for that codebase.
                </p>
                <div className="flex gap-2">
                   <span className="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full">Notion</span>
                   <span className="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full">GitHub MCP</span>
                   <span className="px-2 py-1 bg-muted text-muted-foreground text-xs rounded-full">Coming: Linear, Figma, Slack</span>
                </div>
              </motion.div>
            </div>

          </div>
        </div>
      </section>

      {/* Built for Teams and Enterprises Section */}
      <section className="relative z-10 bg-background py-24">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
           <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl font-bold text-foreground mb-4">Built for teams and enterprises</h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
             <div className="space-y-8">
                <div className="space-y-4">
                   <h3 className="text-xl font-bold flex items-center gap-2">
                      <Users className="w-5 h-5 text-primary" />
                      For engineering teams
                   </h3>
                   <ul className="space-y-2 text-muted-foreground ml-2">
                      <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-primary" /> Shared spaces per repo</li>
                      <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-primary" /> Clear history of chat and agent runs</li>
                      <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-primary" /> Works with real tools like GitHub and Notion</li>
                   </ul>
                </div>
                
                <div className="space-y-4">
                   <h3 className="text-xl font-bold flex items-center gap-2">
                      <Shield className="w-5 h-5 text-primary" />
                      For enterprises
                   </h3>
                    <ul className="space-y-2 text-muted-foreground ml-2">
                      <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-primary" /> Open source platform (AGPL 3)</li>
                      <li className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-primary" /> Bring your own OSS coding model</li>
                      <li className="text-sm border-l-2 border-primary/20 pl-3 py-1 mt-2">
                         "We provide an open source multimodal coding model adapted from the best DeepSeek OSS models, with vision capability, that you can deploy on your infra for sensitive code."
                      </li>
                      <li className="flex items-center gap-2 mt-2"><div className="w-1.5 h-1.5 rounded-full bg-primary" /> Hybrid deployment supported</li>
                   </ul>
                   <a href="mailto:contact@umans.ai" className="inline-block text-sm font-semibold text-primary hover:underline">
                      Talk to us about enterprise options &rarr;
                   </a>
                </div>

                <div className="space-y-4">
                   <h3 className="text-xl font-bold flex items-center gap-2">
                      <Layout className="w-5 h-5 text-primary" />
                      Model agnostic
                   </h3>
                    <p className="text-muted-foreground text-sm">
                       Gemini 3 Pro, GPT 5.1, Claude Sonnet 4.5 and Haiku 4.5, OpenAI Codex and other frontier models. You are not locked into a single vendor.
                    </p>
                </div>
             </div>

             <div className="bg-muted/20 rounded-2xl p-8 border border-border/50 flex flex-col items-center justify-center gap-8">
                <div className="flex flex-wrap justify-center gap-4">
                   <div className="bg-background border border-border px-4 py-2 rounded-lg shadow-sm font-medium text-sm flex items-center gap-2">
                      <Code className="w-4 h-4" /> Open Source
                   </div>
                   <div className="bg-background border border-border px-4 py-2 rounded-lg shadow-sm font-medium text-sm flex items-center gap-2">
                      <Shield className="w-4 h-4" /> Self Hosted Option
                   </div>
                </div>
                
                <div className="text-center space-y-2">
                   <div className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Supported Models</div>
                   <div className="flex flex-wrap justify-center gap-3">
                      {['GPT-5', 'Claude 3.7', 'Gemini 2.0', 'DeepSeek'].map(model => (
                         <span key={model} className="px-3 py-1 bg-background/50 border border-border/50 rounded-full text-xs text-foreground/80">
                            {model}
                         </span>
                      ))}
                   </div>
                </div>
             </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="relative z-10 bg-muted/30 py-24 scroll-mt-24">
        <div className="mx-auto max-w-6xl px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-8"
          >
            <h2 className="text-3xl font-bold text-foreground mb-2">Pricing</h2>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            viewport={{ once: true }}
            className="mb-6 flex justify-center"
          >
            <div className="inline-flex items-center rounded-full border border-border/60 bg-card/80 p-1 text-sm font-medium shadow-sm backdrop-blur">
              {(['monthly', 'yearly'] as const).map((cycle) => (
                <button
                  key={cycle}
                  type="button"
                  onClick={() => setBillingCycle(cycle)}
                  aria-pressed={billingCycle === cycle}
                  className={`rounded-full px-4 py-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/50 ${
                    billingCycle === cycle
                      ? 'bg-primary text-primary-foreground shadow-md'
                      : 'text-muted-foreground hover:text-foreground hover:bg-muted/30'
                  }`}
                >
                  {cycle === 'monthly' ? 'Monthly' : 'Yearly'}
                </button>
              ))}
            </div>
          </motion.div>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 xl:grid-cols-4 items-stretch">
            {pricingPlans.map((plan, index) => {
              const activePricing = plan.pricing[billingCycle];
              const isEnterprise = plan.name === 'Enterprise';
              const buttonClasses =
                plan.ctaVariant === 'primary'
                  ? 'mt-8 inline-flex w-full items-center justify-center rounded-md bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary'
                  : 'mt-8 inline-flex w-full items-center justify-center rounded-md border border-border/60 bg-background px-6 py-3 text-sm font-semibold text-foreground shadow-sm transition-colors hover:border-border focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary';

              return (
                <motion.div
                  key={plan.name}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.1 * index }}
                  viewport={{ once: true }}
                  className={`group relative flex h-full flex-col rounded-2xl border bg-gradient-to-br from-card to-card/80 p-8 shadow-lg transition-all duration-300 hover:shadow-xl backdrop-blur-sm ${
                    plan.popular 
                      ? 'border-primary ring-1 ring-primary/20 from-primary/5 shadow-xl md:scale-105 z-10' 
                      : 'border-border/50 hover:border-border/80'
                  }`}
                >
                  {plan.popular && (
                    <span className="pointer-events-none absolute right-4 top-4 inline-flex items-center rounded-full bg-primary text-primary-foreground px-3 py-1 text-xs font-semibold shadow-sm">
                      Most popular
                    </span>
                  )}

                  <div className="mt-4 space-y-2">
                    <h3 className="text-xl font-bold text-foreground">{plan.name}</h3>
                    <p className="text-sm text-muted-foreground min-h-[40px]">{plan.tagline}</p>
                  </div>

                  <div className="mt-6">
                    <div className="flex items-baseline gap-2">
                      <p className={`${isEnterprise ? 'text-2xl' : 'text-4xl whitespace-nowrap'} font-bold text-foreground`}>{activePricing.amount}</p>
                      <span className={`text-sm text-muted-foreground ${isEnterprise ? '' : 'whitespace-nowrap'}`}>{activePricing.descriptor}</span>
                    </div>
                  </div>

                  <p className="mt-4 text-sm text-muted-foreground min-h-[60px]">{plan.description}</p>

                  <ul className="mt-6 space-y-2 text-sm text-muted-foreground flex-grow">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-start gap-3">
                        <Check className="shrink-0 mt-1 h-4 w-4 text-primary" />
                        <span className="leading-relaxed">{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <div className="mt-8">
                    {plan.name === 'Solo' || plan.name === 'Pro' ? (
                      <button
                        type="button"
                        onClick={() => startCheckout(plan.name.toLowerCase() as 'solo' | 'pro')}
                        disabled={checkoutLoading === (plan.name.toLowerCase() as 'solo' | 'pro')}
                        className={`${buttonClasses} ${checkoutLoading === (plan.name.toLowerCase() as 'solo' | 'pro') ? 'opacity-70 cursor-not-allowed' : ''}`}
                      >
                        {plan.ctaLabel}
                      </button>
                    ) : plan.ctaType === 'internal' ? (
                      <Link href={plan.ctaHref} className={buttonClasses}>
                        {plan.ctaLabel}
                      </Link>
                    ) : (
                      <a href={plan.ctaHref} target="_blank" rel="noopener noreferrer" className={buttonClasses}>
                        {plan.ctaLabel}
                      </a>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Open Source Strip */}
      <section className="relative z-10 bg-background border-t border-border py-12">
        <div className="mx-auto max-w-7xl px-6 lg:px-8 flex flex-col md:flex-row items-center justify-between gap-6">
           <div className="flex items-center gap-4">
              <div className="p-3 bg-muted rounded-full">
                 <IconUmansLogo className="w-6 h-6" /> 
              </div>
              <div>
                 <h3 className="font-bold text-lg">Umans is open source</h3>
                 <p className="text-muted-foreground text-sm">Published under AGPL 3 license.</p>
              </div>
           </div>
           <div className="flex items-center gap-4">
              <a href="https://github.com/umans/umans" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-sm font-medium hover:text-primary transition-colors">
                 <Code className="w-4 h-4" /> Contribute on GitHub
              </a>
               <a href="https://docs.umans.ai" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 text-sm font-medium hover:text-primary transition-colors">
                 <FileText className="w-4 h-4" /> Documentation
              </a>
           </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-border bg-muted/20 py-8">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="flex flex-col items-center justify-between space-y-4 sm:flex-row sm:space-y-0"
          >
            <p className="text-sm text-muted-foreground">
              © {new Date().getFullYear()} Umans. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
               <a href="#" className="text-sm text-muted-foreground hover:text-foreground">Built in public with our community.</a>
               <Link
                href="/privacy"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Privacy Policy
              </Link>
              <Link
                href="/terms"
                className="text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                Terms of Service
              </Link>
            </div>
          </motion.div>
        </div>
      </footer>
    </div>
  );
}