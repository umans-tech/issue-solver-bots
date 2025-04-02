'use client';

import { useState } from 'react';
import { Button } from './ui/button';
import { XIcon } from './icons';
import { cn } from '@/lib/utils';

interface ImagePreviewProps {
  src: string;
  alt: string;
  className?: string;
}

export function ImagePreview({ src, alt, className }: ImagePreviewProps) {
  const [isFullPage, setIsFullPage] = useState(false);

  return (
    <div className={cn(
      "relative w-full overflow-hidden",
      isFullPage && "fixed inset-0 z-50 bg-background/95 backdrop-blur-sm flex items-start justify-center p-8 overflow-y-auto"
    )} onClick={(e) => {
      if (isFullPage && e.target === e.currentTarget) {
        setIsFullPage(false);
      }
    }}>
      <div
        className={cn(
          "cursor-pointer transition-transform hover:scale-[1.02]",
          isFullPage && "min-w-[800px] w-fit max-w-[95vw] max-h-[95vh] mx-auto"
        )}
        onClick={(e) => {
          e.stopPropagation();
          setIsFullPage(!isFullPage);
        }}
      >
        <img
          src={src}
          alt={alt}
          className={cn(
            "w-full h-fit",
            isFullPage ? "object-contain" : "max-w-full"
          )}
        />
      </div>
      {isFullPage && (
        <Button
          onClick={(e) => {
            e.stopPropagation();
            setIsFullPage(false);
          }}
          variant="ghost"
          size="icon"
          className="fixed top-4 right-4"
        >
          <XIcon size={16} />
        </Button>
      )}
    </div>
  );
} 