/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: {
      allowedOrigins: ["localhost:3000", "*.vercel.app"],
    },
  },
  output: 'standalone',
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': '.',
    };
    return config;
  },
  images: {
    domains: [
      'avatar.vercel.sh',
      'lh3.googleusercontent.com', // Google profile images
      'www.gravatar.com', // Gravatar images
    ],
  },
};

module.exports = nextConfig; 