import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  experimental: {
  },
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
