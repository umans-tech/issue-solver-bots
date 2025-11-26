import type { SiteConfig } from '../types';

const siteConfig: SiteConfig = {
  website: 'https://blog.umans.ai',
  avatar: {
    src: '/umans-u-logo.svg',
    alt: 'Umans AI'
  },
  title: 'Umans AI Blog',
  subtitle: 'Field notes on working with AI in real software teams.',
  description: 'Notes on collaborative AI teammates, consistency, and the tooling that keeps teams aligned.',
  image: {
    src: '/umans-logo.svg',
    alt: 'Umans AI'
  },
  headerNavLinks: [
    { text: 'Home', href: '/' },
    { text: 'Blog', href: '/blog' },
    { text: 'About', href: '/about' }
  ],
  footerNavLinks: [
    { text: 'About', href: '/about' },
    { text: 'Blog', href: '/blog' }
  ],
  socialLinks: [
    { text: 'Discord', href: 'https://discord.gg/Q5hdNrk7Rw' },
    { text: 'X', href: 'https://x.com/umans_ai' },
    { text: 'LinkedIn', href: 'https://www.linkedin.com/company/umans-ai' }
  ],
  hero: {
    title: 'Building software with AI, together',
    text: 'Experiments, research, and honest takes on using agents in production teams.',
    actions: [
      { text: 'Read the latest', href: '/blog/consistency-matters' },
      { text: 'About the team', href: '/about' }
    ]
  },
  subscribe: {
    enabled: false,
    title: '',
    text: '',
    form: { action: '#' }
  },
  postsPerPage: 8,
  projectsPerPage: 8
};

export default siteConfig;
