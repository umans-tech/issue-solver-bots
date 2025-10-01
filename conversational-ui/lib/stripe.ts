import Stripe from 'stripe';

let _stripe: Stripe | null = null;
export function getStripe(): Stripe {
  if (!_stripe) {
    if (!process.env.STRIPE_SECRET_KEY) {
      throw new Error('STRIPE_SECRET_KEY is not set');
    }
    _stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
  }
  return _stripe;
}

export type PlanKey = 'solo' | 'pro';
export type BillingCycle = 'monthly' | 'yearly';

// Map plans to Stripe price lookup keys
const lookupKeyMap: Record<PlanKey, Record<BillingCycle, string>> = {
  solo: {
    monthly: 'solo_monthly',
    yearly: 'solo_yearly',
  },
  pro: {
    monthly: 'pro_monthly',
    yearly: 'pro_yearly',
  },
};

const priceCache = new Map<string, string>();

export async function getPriceId(plan: PlanKey, cycle: BillingCycle): Promise<string> {
  const lookupKey = lookupKeyMap[plan]?.[cycle];
  if (!lookupKey) {
    throw new Error(`Missing Stripe price lookup key for ${plan}/${cycle}`);
  }

  const cached = priceCache.get(lookupKey);
  if (cached) {
    return cached;
  }

  const stripe = getStripe();
  const prices = await stripe.prices.list({
    lookup_keys: [lookupKey],
    active: true,
    limit: 1,
  });

  const price = prices.data?.[0];
  if (!price?.id) {
    throw new Error(`Stripe price not found for lookup key ${lookupKey}`);
  }

  priceCache.set(lookupKey, price.id);
  return price.id;
}


