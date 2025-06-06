'use client';

import Image from 'next/image';
import { useState } from 'react';
import { cn } from '@/lib/utils';
import { getGravatarUrl, getInitials } from '@/lib/avatar-utils';
import { generatePastelColor } from '@/lib/utils';

interface AvatarProps {
  user: {
    image?: string | null;
    name?: string | null;
    email?: string | null;
  };
  size?: number;
  className?: string;
}

export function Avatar({ user, size = 24, className }: AvatarProps) {
  const [imageError, setImageError] = useState(false);
  const [gravatarError, setGravatarError] = useState(false);
  
  const { image: googleImage, name, email } = user;
  const initials = getInitials(name, email);
  const gradientBackground = generatePastelColor(email || name || '');
  
  // If we have a Google image and it hasn't failed, show it
  if (googleImage && !imageError) {
    return (
      <Image
        src={googleImage}
        alt={`${name || email || 'User'} avatar`}
        width={size}
        height={size}
        className={cn('rounded-full', className)}
        onError={() => setImageError(true)}
      />
    );
  }
  
  // If Google image failed or doesn't exist, try Gravatar
  if (email && !gravatarError && !imageError) {
    const gravatarUrl = getGravatarUrl(email, size * 2); // 2x for retina
    
    return (
      <Image
        src={gravatarUrl}
        alt={`${name || email} avatar`}
        width={size}
        height={size}
        className={cn('rounded-full', className)}
        onError={() => setGravatarError(true)}
      />
    );
  }
  
  // Fallback to initials with gradient
  return (
    <div
      className={cn(
        'flex items-center justify-center rounded-full text-white font-medium',
        className
      )}
      style={{
        width: size,
        height: size,
        backgroundImage: gradientBackground,
        fontSize: `${size * 0.4}px`, // Scale font size with avatar size
      }}
    >
      {initials}
    </div>
  );
} 