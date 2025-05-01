'use client';

import Link from 'next/link';
import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';

export default function LandingPage() {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });
  const learnMoreRef = useRef<HTMLDivElement>(null);

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

  const scrollToLearnMore = () => {
    learnMoreRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Dynamic gradient background */}
      <div 
        className="absolute inset-0 transition-opacity duration-500"
        style={{
          background: `radial-gradient(circle at ${mousePosition.x * 100}% ${mousePosition.y * 100}%, 
            rgba(99, 102, 241, 0.15) 0%, 
            rgba(99, 102, 241, 0) 50%)`,
        }}
      />

      {/* Hero Section */}
      <div className="relative z-10 flex min-h-screen flex-col items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-3xl text-center"
        >
          <h1 className="mb-6 text-5xl font-bold tracking-tight text-foreground sm:text-6xl">
            Keep code, concepts & business goals perfectly in-sync
          </h1>
          
          <p className="mb-8 text-lg text-muted-foreground">
            umans.ai is your software's second brain—always aligned with the business, always shipping.
          </p>

          <div className="flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/?from=landing"
              className="rounded-md bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
            >
              Start Building
            </Link>
            <button
              onClick={scrollToLearnMore}
              className="rounded-md bg-secondary px-6 py-3 text-sm font-semibold text-secondary-foreground shadow-sm hover:bg-secondary/90"
            >
              Learn More
            </button>
          </div>
        </motion.div>
      </div>

      {/* Learn More Section */}
      <div ref={learnMoreRef} className="relative z-10 bg-background py-24">
        <div className="mx-auto max-w-7xl px-6 lg:px-8">
          <div className="mx-auto max-w-2xl lg:max-w-none">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
              className="grid grid-cols-1 gap-8 lg:grid-cols-2"
            >
              {/* Problem Statement */}
              <div className="rounded-2xl bg-card p-8 shadow-sm">
                <h2 className="text-2xl font-bold text-foreground mb-4">The Problem</h2>
                <p className="text-muted-foreground">
                  Teams that have moved beyond an MVP hit a wall of complexity:
                </p>
                <ul className="mt-4 space-y-2 text-muted-foreground">
                  <li>• Low predictability of delivering new changes → slipping roadmaps</li>
                  <li>• Mis-alignment between business intent & code reality → re-work</li>
                  <li>• Rising accidental complexity & bureaucracy → higher cost-of-change</li>
                </ul>
              </div>

              {/* Solution */}
              <div className="rounded-2xl bg-card p-8 shadow-sm">
                <h2 className="text-2xl font-bold text-foreground mb-4">The Solution</h2>
                <p className="text-muted-foreground mb-4">
                  umans.ai is a multi-AI-agent platform that:
                </p>
                <ul className="space-y-2 text-muted-foreground">
                  <li>• Captures & evolves the shared conceptual model of your software</li>
                  <li>• Guides every next increment from design → deploy → observe</li>
                  <li>• Boosts DORA metrics & confidence while shrinking cost-of-change</li>
                </ul>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
} 