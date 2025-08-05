'use client';

import Link from 'next/link';
import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { IconUmansLogo } from '@/components/icons';
import { LandingNavbar } from '@/components/landing-navbar';
import { Brain, Zap, Users, Bot, BarChart3, Rocket, FlaskConical, FileText, Settings, DollarSign, Calendar, MessageSquare, Mail } from 'lucide-react';

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

      {/* Pricing Transparency Section */}
      <div className="relative z-10 bg-muted/30 py-24">
        <div className="mx-auto max-w-4xl px-6 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl font-bold text-foreground mb-4">Transparent Pricing</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              We believe in honest, transparent pricing. Help us build the right model for you.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 gap-8 lg:grid-cols-2">
            {/* Current Status */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.1 }}
              viewport={{ once: true }}
              className="group landing-feature-card rounded-2xl bg-gradient-to-br from-card to-card/80 p-8 shadow-lg border border-border/50 hover:shadow-xl hover:border-border/80 transition-all duration-300 backdrop-blur-sm"
            >
              <div className="mb-4">
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 text-sm font-medium">
                  <DollarSign className="w-4 h-4 mr-2" />
                  Currently Free
                </div>
              </div>
              <h3 className="text-xl font-bold text-foreground mb-4">While we build something amazing</h3>
              <p className="text-muted-foreground">
                Get full access to all current features while we develop and refine the platform.
                No limits, no hidden costs - just pure innovation.
              </p>
            </motion.div>

            {/* Future Plans */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2 }}
              viewport={{ once: true }}
              className="group landing-feature-card rounded-2xl bg-gradient-to-br from-card to-card/80 p-8 shadow-lg border border-border/50 hover:shadow-xl hover:border-border/80 transition-all duration-300 backdrop-blur-sm"
            >
              <div className="mb-4">
                <div className="inline-flex items-center px-4 py-2 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 text-sm font-medium">
                  <Calendar className="w-4 h-4 mr-2" />
                  Paid Plans Coming
                </div>
              </div>
              <h3 className="text-xl font-bold text-foreground mb-4">Q3-Q4 2025</h3>
              <p className="text-muted-foreground mb-4">
                Early users get special pricing when we launch our subscription model.
                You'll be grandfathered into the best rates.
              </p>
              <div className="inline-flex items-center px-3 py-1 rounded-md bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200 text-xs font-medium">
                Early Access Advantage
              </div>
            </motion.div>
          </div>

          {/* Feedback Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            viewport={{ once: true }}
            className="text-center mt-12"
          >
            <div className="group landing-feature-card rounded-2xl bg-gradient-to-br from-card to-card/80 p-8 shadow-lg border border-border/50 hover:shadow-xl hover:border-border/80 transition-all duration-300 backdrop-blur-sm">
              <div className="mb-6">
                <MessageSquare className="w-8 h-8 text-primary mx-auto mb-4 group-hover:scale-110 transition-transform duration-300" />
                <h3 className="text-xl font-bold text-foreground mb-2">Help Shape Our Pricing</h3>
                <p className="text-muted-foreground">
                  Your input matters. Tell us what pricing model would work best for your team.
                </p>
              </div>

              <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
                <a
                  href="https://docs.google.com/forms/d/e/1FAIpQLScKnZwyFyizdnt3gBKOY7EFdnIHnuYWYGaaxqMpV1fWQk-szw/viewform?usp=header"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="rounded-md bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary transition-colors"
                >
                  Share Your Feedback
                </a>
                <div className="flex items-center text-sm text-muted-foreground">
                  <Mail className="w-4 h-4 mr-2" />
                  Questions? <a href="mailto:contact@umans.ai" className="ml-1 text-primary hover:underline">contact@umans.ai</a>
                </div>
              </div>
            </div>
          </motion.div>
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