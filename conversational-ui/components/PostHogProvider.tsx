"use client"

import posthog from "posthog-js"
import { PostHogProvider as PHProvider } from "posthog-js/react"
import { useEffect } from "react"

export function PostHogProvider({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const runtimeCfg = (globalThis as any).__RUNTIME_CONFIG__ || {}
    const posthogKey = runtimeCfg.POSTHOG_KEY || ""
    if (!posthogKey) {
      if (process.env.NODE_ENV === "development") {
        // eslint-disable-next-line no-console
        console.warn("PostHog key missing in runtime config; analytics disabled")
      }
      return
    }
    posthog.init(posthogKey, {
      api_host: "/ingest",
      defaults: '2025-05-24',
      capture_exceptions: true,
      debug: process.env.NODE_ENV === "development",
    })
  }, [])

  return <PHProvider client={posthog}>{children}</PHProvider>
}