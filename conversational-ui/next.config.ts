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
    ],
  },
  env: {
    AUTH_TRUST_HOST: 'true',
  },
};

export default nextConfig;
