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

// Map plans to Stripe price IDs via env vars for simplicity
export const priceMap: Record<PlanKey, Record<BillingCycle, string>> = {
  solo: {
    monthly: process.env.STRIPE_PRICE_SOLO_MONTHLY || '',
    yearly: process.env.STRIPE_PRICE_SOLO_YEARLY || '',
  },
  pro: {
    monthly: process.env.STRIPE_PRICE_PRO_MONTHLY || '',
    yearly: process.env.STRIPE_PRICE_PRO_YEARLY || '',
  },
};

export function getPriceId(plan: PlanKey, cycle: BillingCycle): string {
  const id = priceMap[plan]?.[cycle];
  if (!id) throw new Error(`Missing Stripe price ID for ${plan}/${cycle}`);
  return id;
}


