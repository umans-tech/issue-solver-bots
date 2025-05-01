/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverActions: {
      allowedOrigins: ['localhost:3000'],
    },
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': '.',
    };
    return config;
  },
  images: {
    domains: ['avatar.vercel.sh'],
  },
  
  // Add redirects for domain-based routing
  async redirects() {
    return [
      {
        // Redirect umans.ai root to landing page
        source: '/',
        destination: '/landing',
        has: [
          {
            type: 'host',
            value: 'umans.ai',
          }
        ],
        // Permanent: false makes it a temporary redirect (307)
        permanent: false,
      },
      {
        // Special case for when clicking "Start Building"
        // This redirects to app.umans.ai
        source: '/',
        destination: 'https://app.umans.ai',
        has: [
          {
            type: 'host',
            value: 'umans.ai',
          },
          {
            type: 'query',
            key: 'from',
            value: 'landing',
          }
        ],
        permanent: false,
      }
    ];
  },
};

module.exports = nextConfig; 