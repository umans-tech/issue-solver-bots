import { NextResponse } from 'next/server';
import { z } from 'zod';
import { db } from '@/lib/db';
import { waitlistSignups } from '@/lib/db/schema';
import PostHogClient from '@/lib/posthog';

const signupSchema = z.object({
  waitlist_id: z.string(),
  email: z.string().email(),
  role: z.string().optional(),
  goal: z.string().optional(),
  repos_count: z.string().optional(),
  need_vpc: z.boolean().optional(),
  pricing_expectation: z.string().optional(),
  repo_link: z.string().optional(),
  utm: z.record(z.string()).optional(),
  referrer: z.string().optional(),
  page_path: z.string().optional(),
});

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const validatedData = signupSchema.parse(body);

    const {
      waitlist_id,
      email,
      role,
      goal,
      repos_count,
      need_vpc,
      pricing_expectation,
      repo_link,
      utm,
      referrer,
      page_path,
    } = validatedData;

    try {
      await db.insert(waitlistSignups).values({
        waitlistId: waitlist_id,
        email: email.toLowerCase(),
        role,
        goal,
        reposCount: repos_count,
        needVpc: need_vpc,
        repoLink: repo_link,
        utmSource: utm?.source,
        utmMedium: utm?.medium,
        utmCampaign: utm?.campaign,
        utmContent: utm?.content,
        utmTerm: utm?.term,
        referrer,
        pagePath: page_path,
      });
    } catch (error: any) {
      // Handle unique constraint violation (duplicate signup)
      // code 23505 is unique_violation in Postgres
      if (error.code === '23505') {
          // Already signed up, just return success
          return NextResponse.json({ success: true, message: 'Already on the list' });
      }
      console.error('Database error:', error);
      throw error;
    }

    // Server-side PostHog tracking
    try {
      const posthog = PostHogClient();
      posthog.capture({
        distinctId: email.toLowerCase(),
        event: 'submit_waitlist',
        properties: {
          waitlist_id,
          pricing_expectation,
          role,
          repos_count,
          need_vpc,
          email_domain: email.split('@')[1],
          page_path,
          referrer,
          ...utm,
        },
      });
      await posthog.shutdown();
    } catch (phError) {
      console.error('PostHog tracking error:', phError);
      // Don't fail the request if tracking fails
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Waitlist signup error:', error);
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
  }
}