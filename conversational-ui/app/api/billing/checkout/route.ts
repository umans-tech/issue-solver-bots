import { NextResponse } from 'next/server';
import { auth } from '@/app/(auth)/auth';
import { getStripe, getPriceId, type PlanKey, type BillingCycle } from '@/lib/stripe';
import { getUser } from '@/lib/db/queries';

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.email || !session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { plan, cycle }: { plan: PlanKey; cycle: BillingCycle } = await req.json();
  if (!plan || !cycle) {
    return NextResponse.json({ error: 'Missing plan/cycle' }, { status: 400 });
  }

  const price = getPriceId(plan, cycle);
  const [dbUser] = await getUser(session.user.email);

  const stripe = getStripe();
  const baseUrl = process.env.NEXTAUTH_URL || process.env.NEXT_PUBLIC_APP_URL || process.env.APP_URL || 'http://localhost:3000';

  const checkout = await stripe.checkout.sessions.create({
    mode: 'subscription',
    payment_method_types: ['card'],
    line_items: [{ price, quantity: 1 }],
    success_url: `${baseUrl}/?billing=success`,
    cancel_url: `${baseUrl}/pricing?billing=cancelled`,
    customer_email: dbUser?.email || session.user.email,
    client_reference_id: session.user.id,
    metadata: { userId: session.user.id, plan, cycle },
  });

  return NextResponse.json({ url: checkout.url });
}


