'use client';

import Link from 'next/link';
import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { IconUmansLogo } from '@/components/icons';
import { LandingNavbar } from '@/components/landing-navbar';
import { Brain, Zap, Users, Bot, BarChart3, Rocket, FlaskConical, FileText, Check } from 'lucide-react';

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

  const scrollToFeatures = () => {
    featuresRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('monthly');

  const pricingPlans = [
    {
      name: 'Free',
      tagline: 'Great for exploring Umans',
      description: 'Spin up our browser-based coding agents and see how far the platform takes you.',
      features: [
        '5 daily agent credits (up to 50 monthly)',
        'GPT-5, Claude Sonnet & Claude Code in-browser sessions',
        'Auto-generated docs & diagrams for a personal space',
      ],
      ctaLabel: 'Start for free',
      ctaHref: '/go-to-app',
      ctaType: 'internal',
      ctaVariant: 'primary',
      pricing: {
        monthly: { amount: '$0', descriptor: 'per user / month' },
        yearly: { amount: '$0', descriptor: 'per user / month' },
      },
    },
    {
      name: 'Individual',
      tagline: 'For solo founders and indie hackers',
      description: 'Level up with more credits and access to our newest GPT-5 powered workflows.',
      features: [
        '300 monthly agent credits',
        'Extended runs with GPT-5, Claude Sonnet & Claude Code',
        'Personal workspace with persistent context & docs',
      ],
      ctaLabel: 'Get Individual',
      ctaHref: 'https://buy.stripe.com/individual-plan-link',
      ctaType: 'external',
      ctaVariant: 'secondary',
      pricing: {
        monthly: { amount: '$24', descriptor: 'per user / month' },
        yearly: { amount: '$19', descriptor: 'per user / month' },
      },
    },
    {
      name: 'Team',
      tagline: 'Built for product teams that ship together',
      description: 'Share context across teammates and keep everyone aligned with living docs.',
      features: [
        '600 shared monthly agent credits',
        'Shared spaces with cross-conversation memory',
        'Seats for up to 5 collaborators (per-user pricing)',
      ],
      ctaLabel: 'Get Team',
      ctaHref: 'https://buy.stripe.com/team-plan-link',
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
      ctaLabel: 'Talk to sales',
      ctaHref: 'mailto:contact@umans.ai',
      ctaType: 'external',
      ctaVariant: 'secondary',
      pricing: {
        monthly: { amount: 'Contact us', descriptor: 'Let’s design the right package' },
        yearly: { amount: 'Contact us', descriptor: 'Let’s design the right package' },
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
      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center p-4 pt-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-4xl text-center"
        >
          <h1 className="mb-6 text-5xl font-bold tracking-tight text-foreground sm:text-6xl">
          Deliver Value, Not Just Code
          </h1>
          
          <p className="mb-6 text-xl text-muted-foreground max-w-3xl mx-auto">
          Bridge the gap between what your system does, what business needs, and what your team plans to build.
          </p>


          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center mb-6">
            <Link
              href="/go-to-app"
              className="rounded-md bg-primary px-8 py-3 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              Start Building
            </Link>
            <button
              onClick={scrollToFeatures}
              className="rounded-md bg-secondary px-8 py-3 text-sm font-semibold text-secondary-foreground shadow-sm hover:bg-secondary/90"
            >
              Learn More
            </button>
          </div>

          <div className="inline-flex items-center px-4 py-2 rounded-full bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200 text-sm font-medium">
            <Rocket className="w-4 h-4 mr-2" />
            Currently in Early Access (Alpha)
          </div>
        </motion.div>
      </div>

      {/* Current Capabilities Section */}
      <div ref={featuresRef} className="relative z-10 bg-background py-24">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl font-bold text-foreground mb-4">What You Get Today</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              AI agents that understand your codebase and collaborate with your team
            </p>
          </motion.div>

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-3 mb-16">
            {/* AI-Assisted Software Delivery */}
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
              <h3 className="text-xl font-bold text-foreground mb-4">Deep Codebase Understanding</h3>
              <p className="text-muted-foreground">
                Chat with AI that truly understands your architecture, generates insightful diagrams, and helps your team navigate even the most complex codebases with confidence.
              </p>
            </motion.div>

            {/* Automated Issue Resolution */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              viewport={{ once: true }}
              className="group landing-feature-card rounded-2xl bg-gradient-to-br from-card to-card/80 p-8 shadow-lg border border-border/50 hover:shadow-xl hover:border-border/80 transition-all duration-300 backdrop-blur-sm"
            >
              <div className="mb-4">
                <Zap className="w-8 h-8 text-primary group-hover:scale-110 transition-transform duration-300" />
              </div>
              <h3 className="text-xl font-bold text-foreground mb-4">Automated Issue Resolution</h3>
              <p className="text-muted-foreground">
                Delegate small changes, debugging fixes, and medium-sized pull requests to umans.ai remote agents.
              </p>
            </motion.div>

            {/* Team Collaboration */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              viewport={{ once: true }}
              className="group landing-feature-card rounded-2xl bg-gradient-to-br from-card to-card/80 p-8 shadow-lg border border-border/50 hover:shadow-xl hover:border-border/80 transition-all duration-300 backdrop-blur-sm"
            >
              <div className="mb-4">
                <Users className="w-8 h-8 text-primary group-hover:scale-110 transition-transform duration-300" />
              </div>
              <h3 className="text-xl font-bold text-foreground mb-4">Multi-User Collaboration</h3>
              <p className="text-muted-foreground">
                Capture collective knowledge, maintain context across conversations, and ensure everyone stays aligned on what you're building.
              </p>
            </motion.div>
          </div>

        </div>
      </div>

      {/* Vision Section */}
      <div className="relative z-10 bg-muted/30 py-24">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl font-bold text-foreground mb-4">Where We're Going</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              Exploring the future of software delivery
            </p>
          </motion.div>

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
            {/* Specifications-driven Development */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.1 }}
              viewport={{ once: true }}
              className="group landing-feature-card rounded-2xl bg-gradient-to-br from-card to-card/80 p-8 shadow-lg border border-border/50 hover:shadow-xl hover:border-border/80 transition-all duration-300 backdrop-blur-sm"
            >
              <div className="mb-4">
                <FileText className="w-8 h-8 text-primary group-hover:scale-110 transition-transform duration-300" />
              </div>
              <h3 className="text-xl font-bold text-foreground mb-4">Collaborative Executable Modeling</h3>
              <p className="text-muted-foreground">
                Transform business scenarios, examples, and specifications into a new level of coding abstraction where requirements become executable blueprints.
              </p>
            </motion.div>

            {/* Production Intelligence */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              viewport={{ once: true }}
              className="group landing-feature-card rounded-2xl bg-gradient-to-br from-card to-card/80 p-8 shadow-lg border border-border/50 hover:shadow-xl hover:border-border/80 transition-all duration-300 backdrop-blur-sm"
            >
              <div className="mb-4">
                <BarChart3 className="w-8 h-8 text-primary group-hover:scale-110 transition-transform duration-300" />
              </div>
              <h3 className="text-xl font-bold text-foreground mb-4">Production Intelligence</h3>
              <p className="text-muted-foreground">
                Monitor your applications in real-time with AI agents that analyze incidents, predict issues, and suggest mitigation strategies before problems escalate.
              </p>
            </motion.div>

            {/* Complex Task Automation */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              viewport={{ once: true }}
              className="group landing-feature-card rounded-2xl bg-gradient-to-br from-card to-card/80 p-8 shadow-lg border border-border/50 hover:shadow-xl hover:border-border/80 transition-all duration-300 backdrop-blur-sm"
            >
              <div className="mb-4">
                <Bot className="w-8 h-8 text-primary group-hover:scale-110 transition-transform duration-300" />
              </div>
              <h3 className="text-xl font-bold text-foreground mb-4">Complex Task Automation</h3>
              <p className="text-muted-foreground">
                Scale beyond simple fixes with intelligent agents that handle sophisticated refactoring, architecture migrations, and multi-service deployments.
              </p>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            viewport={{ once: true }}
            className="text-center mt-12"
          >
            <div className="inline-flex items-center px-6 py-3 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 text-sm font-medium">
              <FlaskConical className="w-4 h-4 mr-2" />
              Soon: Private Beta with expanded capabilities
            </div>
          </motion.div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="relative z-10 bg-background py-24">
        <div className="mx-auto max-w-4xl px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl font-bold text-foreground mb-6">
              Ready to transform your software delivery?
            </h2>
            <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
              Join teams that are already using AI agents to bridge the gap between 
              business understanding and technical implementation.
            </p>
            <Link
              href="/go-to-app"
              className="rounded-md bg-primary px-8 py-4 text-base font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              Start Building
            </Link>
          </motion.div>
        </div>
      </div>

      {/* Pricing Section */}
      <div className="relative z-10 bg-muted/30 py-24">
        <div className="mx-auto max-w-6xl px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-8"
          >
            <h2 className="text-3xl font-bold text-foreground mb-4">Pricing that grows with your team</h2>
            <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
              Pick the plan that fits today. Upgrade only when you need more collaboration and guidance.
            </p>
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
                  className={`rounded-full px-4 py-2 transition-colors ${
                    billingCycle === cycle
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  {cycle === 'monthly' ? 'Monthly' : 'Yearly'}
                </button>
              ))}
            </div>
          </motion.div>

          <motion.p
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.15 }}
            viewport={{ once: true }}
            className="text-center text-sm text-muted-foreground mb-12"
          >
            All plans include GPT-5, Claude Sonnet, Claude Code, and upcoming agents inside the Umans conversational workspace.
          </motion.p>

          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 xl:grid-cols-4">
            {pricingPlans.map((plan, index) => {
              const activePricing = plan.pricing[billingCycle];
              const buttonClasses =
                plan.ctaVariant === 'primary'
                  ? 'mt-8 inline-flex items-center justify-center rounded-md bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-sm transition-colors hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary'
                  : 'mt-8 inline-flex items-center justify-center rounded-md border border-border/60 bg-background px-6 py-3 text-sm font-semibold text-foreground shadow-sm transition-colors hover:border-border focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary';

              return (
                <motion.div
                  key={plan.name}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: 0.1 * index }}
                  viewport={{ once: true }}
                  className={`group flex h-full flex-col rounded-2xl border border-border/50 bg-gradient-to-br from-card to-card/80 p-8 shadow-lg transition-all duration-300 hover:border-border/80 hover:shadow-xl backdrop-blur-sm ${plan.popular ? 'border-primary/70 shadow-primary/30' : ''}`}
                >
                  {plan.popular && (
                    <span className="inline-flex w-fit items-center rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                      Most popular
                    </span>
                  )}

                  <div className="mt-4 space-y-2">
                    <h3 className="text-xl font-bold text-foreground">{plan.name}</h3>
                    <p className="text-sm text-muted-foreground">{plan.tagline}</p>
                  </div>

                  <div className="mt-6">
                    <div className="flex items-baseline gap-2">
                      <p className="text-4xl font-bold text-foreground">{activePricing.amount}</p>
                      <span className="text-sm text-muted-foreground">{activePricing.descriptor}</span>
                    </div>
                  </div>

                  <p className="mt-4 text-sm text-muted-foreground">{plan.description}</p>

                  <div className="mt-6 space-y-3 text-sm text-muted-foreground">
                    {plan.features.map((feature) => (
                      <div key={feature} className="flex items-start gap-3">
                        <span className="flex h-5 w-5 items-center justify-center rounded-full border border-primary/40 bg-primary/10 text-primary">
                          <Check className="h-3 w-3" />
                        </span>
                        <span>{feature}</span>
                      </div>
                    ))}
                  </div>

                  <div className="mt-auto">
                    {plan.ctaType === 'internal' ? (
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
      </div>

      {/* Footer */}
      <footer className="relative z-10 border-t border-border bg-background py-8">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="flex flex-col items-center justify-center space-y-4 sm:flex-row sm:space-y-0 sm:space-x-8"
          >
            <div className="flex space-x-6">
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
            <p className="text-sm text-muted-foreground">
              © {new Date().getFullYear()} Umans. All rights reserved.
            </p>
          </motion.div>
        </div>
      </footer>
    </div>
  );
} 
