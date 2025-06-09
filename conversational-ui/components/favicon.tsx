'use client';

import { useState } from 'react';
import { Earth } from 'lucide-react';
import { getFaviconUrl } from '@/lib/utils';

interface FaviconProps {
  url: string;
  className?: string;
  alt?: string;
  fallbackIcon?: React.ReactNode;
}

/**
 * Centralized favicon component with robust fallback handling
 * Ensures consistent favicon display across all web search results
 */
export const Favicon = ({ 
  url, 
  className = "w-4 h-4 rounded-sm", 
  alt = "",
  fallbackIcon 
}: FaviconProps) => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const fallbackUrls = getFaviconUrl(url);
  
  if (!fallbackUrls.length) {
    return (
      <div className={`${className} flex items-center justify-center bg-muted/20 rounded-sm`}>
        {fallbackIcon || <Earth className="w-3 h-3 text-muted-foreground" />}
      </div>
    );
  }
  
  const handleError = () => {
    if (currentIndex < fallbackUrls.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      // All fallbacks failed, show fallback icon
      setCurrentIndex(fallbackUrls.length);
    }
  };
  
  if (currentIndex >= fallbackUrls.length) {
    return (
      <div className={`${className} flex items-center justify-center bg-muted/20 rounded-sm`}>
        {fallbackIcon || <Earth className="w-3 h-3 text-muted-foreground" />}
      </div>
    );
  }
  
  return (
    <img 
      src={fallbackUrls[currentIndex]} 
      alt={alt}
      className={className}
      onError={handleError}
      loading="lazy"
    />
  );
}; 