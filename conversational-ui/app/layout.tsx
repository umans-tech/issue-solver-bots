import type { Metadata } from 'next';
import { Toaster } from 'sonner';

import { ThemeProvider } from '@/components/theme-provider';
import { TooltipProvider } from '@/components/ui/tooltip';
import { PostHogProvider } from '@/components/PostHogProvider';

import './globals.css';

export const metadata: Metadata = {
  metadataBase: new URL('https://chat.umans.ai'),
  title: {
    default: 'umans.ai Platform',
    template: `%s - umans.ai Platform`,
  },
  description:
    'umans.ai empowers teams to deliver predictable, high-quality software aligned with business goals.',
  icons: {
    icon: '/favicon.ico',
    shortcut: '/favicon-16x16.png',
    apple: '/apple-touch-icon.png',
  },
};

export const viewport = {
  maximumScale: 1, // Disable auto-zoom on mobile Safari
};

const LIGHT_THEME_COLOR = 'hsl(0 0% 100%)';
const DARK_THEME_COLOR = 'hsl(240deg 10% 3.92%)';
const THEME_COLOR_SCRIPT = `\
(function() {
  var html = document.documentElement;
  var meta = document.querySelector('meta[name="theme-color"]');
  if (!meta) {
    meta = document.createElement('meta');
    meta.setAttribute('name', 'theme-color');
    document.head.appendChild(meta);
  }
  function updateThemeColor() {
    var isDark = html.classList.contains('dark');
    meta.setAttribute('content', isDark ? '${DARK_THEME_COLOR}' : '${LIGHT_THEME_COLOR}');
  }
  var observer = new MutationObserver(updateThemeColor);
  observer.observe(html, { attributes: true, attributeFilter: ['class'] });
  updateThemeColor();
})();`;

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      // `next-themes` injects an extra classname to the body element to avoid
      // visual flicker before hydration. Hence the `suppressHydrationWarning`
      // prop is necessary to avoid the React hydration mismatch warning.
      // https://github.com/pacocoursey/next-themes?tab=readme-ov-file#with-app
      suppressHydrationWarning
    >
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: THEME_COLOR_SCRIPT,
          }}
        />
        <script
          // Inject runtime config for client-side analytics at request time
          dangerouslySetInnerHTML={{
            __html: `
              window.__RUNTIME_CONFIG__ = {
                POSTHOG_KEY: ${JSON.stringify(process.env.POSTHOG_KEY ?? '')},
                STRIPE_BILLING_PORTAL_URL: ${JSON.stringify(process.env.STRIPE_BILLING_PORTAL_URL ?? '')},
                UMANS_BILLING_SUPPORT_EMAIL: ${JSON.stringify(process.env.UMANS_BILLING_SUPPORT_EMAIL ?? '')}
              };
            `,
          }}
        />
      </head>
      <body className="antialiased">
        <PostHogProvider>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <TooltipProvider>
              <Toaster position="top-center" />
              {children}
            </TooltipProvider>
          </ThemeProvider>
        </PostHogProvider>
      </body>
    </html>
  );
}
