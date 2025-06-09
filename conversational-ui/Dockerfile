# Use multi-stage build for smaller final image
FROM node:20-bullseye-slim AS base

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Set working directory
WORKDIR /app

# Install dependencies only when needed
FROM base AS deps
COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile

# Install Playwright browsers and system dependencies
RUN npx playwright install --with-deps chromium

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next.js collects anonymous telemetry data about general usage.
# Learn more here: https://nextjs.org/telemetry
# Uncomment the following line to disable telemetry during the build.
ENV NEXT_TELEMETRY_DISABLED=1

# Add build arguments
ARG POSTGRES_URL
ENV POSTGRES_URL=${POSTGRES_URL}
ARG REDIS_URL=redis://localhost:6379
ENV REDIS_URL=${REDIS_URL}
ARG OPENAI_API_KEY
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ARG EXA_API_KEY
ENV EXA_API_KEY=${EXA_API_KEY}
ARG EMAIL_API_KEY
ENV EMAIL_API_KEY=${EMAIL_API_KEY}
ARG EMAIL_FROM
ENV EMAIL_FROM=${EMAIL_FROM}

# Build the application (without migrations)
RUN pnpm build:only

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

# Install minimal runtime dependencies for Chromium
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libgtk-3-0 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy Playwright browsers from deps stage
COPY --from=deps /root/.cache/ms-playwright ./playwright-browsers

COPY --from=builder /app/public ./public
COPY --from=builder /app/lib/db ./lib/db
COPY --from=builder /app/node_modules ./node_modules

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
# Critical settings for App Runner
ENV HOST="0.0.0.0"
ENV HOSTNAME="0.0.0.0"
# Playwright browser path
ENV PLAYWRIGHT_BROWSERS_PATH="./playwright-browsers"

EXPOSE 3000

CMD ["node","server.js","--hostname","0.0.0.0"]