import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
  },
  output: 'standalone', // Add this line for containerization
  images: {
    remotePatterns: [
      {
        hostname: 'avatar.vercel.sh',
      },
      {
        hostname: 'lh3.googleusercontent.com', // Google profile images
      },
      {
        hostname: 'www.gravatar.com', // Gravatar images
      },
    ],
  },
  env: {
    AUTH_TRUST_HOST: 'true',
  },
};

export default nextConfig;
