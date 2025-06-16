'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * ErrorBoundary component to catch JavaScript errors anywhere in child component tree
 * and display a fallback UI instead of the component tree that crashed.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    // Update state so the next render will show the fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log the error to the console but prevent it from bubbling up to the browser
    console.error('Error caught by ErrorBoundary (suppressed):', error);
    console.error('Component stack:', errorInfo.componentStack);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      // You can render any custom fallback UI
      return this.props.fallback || (
        <div className="p-4 border border-red-200 dark:border-red-800 rounded-lg bg-background">
          <h3 className="text-sm font-medium text-red-600 dark:text-red-400">
            Something went wrong
          </h3>
          <p className="mt-2 text-sm text-muted-foreground">
            The application encountered an error. Please try again or contact support if the problem persists.
          </p>
        </div>
      );
    }

    return this.props.children;
  }
}