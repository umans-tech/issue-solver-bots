import { createHash } from 'crypto';

/**
 * Generate MD5 hash for Gravatar service
 */
export function generateGravatarHash(email: string): string {
  return createHash('md5')
    .update(email.toLowerCase().trim())
    .digest('hex');
}

/**
 * Generate Gravatar URL for an email
 */
export function getGravatarUrl(email: string, size: number = 80): string {
  const hash = generateGravatarHash(email);
  return `https://www.gravatar.com/avatar/${hash}?s=${size}&d=404`;
}

/**
 * Extract initials from a name or email
 */
export function getInitials(name?: string | null, email?: string | null): string {
  if (name) {
    // Extract initials from full name
    const words = name.trim().split(/\s+/);
    if (words.length >= 2) {
      return (words[0][0] + words[words.length - 1][0]).toUpperCase();
    }
    return words[0][0]?.toUpperCase() || '?';
  }
  
  if (email) {
    // Use first letter of email if no name
    return email[0]?.toUpperCase() || '?';
  }
  
  return '?';
}

/**
 * Generate a consistent color based on a string (email or name)
 */
export function getAvatarColor(str: string): string {
  // Simple hash function to generate consistent colors
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  
  // Convert to HSL for better color distribution
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 65%, 55%)`;
} 