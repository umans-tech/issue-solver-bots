import { headers } from 'next/headers';
import { NextResponse } from 'next/server';
import { getStripe } from '@/lib/stripe';
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import { user } from '@/lib/db/schema';
import { eq } from 'drizzle-orm';

const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;

export async function POST(req: Request) {
  const sig = (await headers()).get('stripe-signature');
  const body = await req.text();

  let event;
  try {
    const stripe = getStripe();
    event = stripe.webhooks.constructEvent(body, sig as string, webhookSecret);
  } catch (err: any) {
    return new NextResponse(`Webhook Error: ${err.message}`, { status: 400 });
  }

  // db client (avoid importing queries to keep low-level update)
  // biome-ignore lint: Forbidden non-null assertion
  const client = postgres(process.env.POSTGRES_URL!);
  const db = drizzle(client);

  switch (event.type) {
    case 'checkout.session.completed': {
      const s = event.data.object as any;
      const userId: string | undefined =
        s.client_reference_id || s.metadata?.userId;
      const stripeCustomerId: string | undefined = s.customer as
        | string
        | undefined;
      const plan = s.metadata?.plan as string | undefined;
      if (userId) {
        await db
          .update(user)
          .set({
            stripeCustomerId: stripeCustomerId ?? undefined,
            plan: (plan as any) || 'free',
            subscriptionStatus: 'active',
          })
          .where(eq(user.id, userId));
      }
      break;
    }
    case 'customer.subscription.updated':
    case 'customer.subscription.created': {
      const sub = event.data.object as any;
      const stripeCustomerId = sub.customer as string;
      const status = sub.status as string;
      // We need to locate user by customer id
      await db
        .update(user)
        .set({ subscriptionStatus: status })
        .where(eq(user.stripeCustomerId, stripeCustomerId));
      break;
    }
    case 'customer.subscription.deleted': {
      const sub = event.data.object as any;
      const stripeCustomerId = sub.customer as string;
      await db
        .update(user)
        .set({ plan: 'free', subscriptionStatus: 'canceled' })
        .where(eq(user.stripeCustomerId, stripeCustomerId));
      break;
    }
    default:
      // ignore
      break;
  }

  return NextResponse.json({ received: true });
}
