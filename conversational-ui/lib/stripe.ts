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

export type PlanKey = 'individual' | 'team';
export type BillingCycle = 'monthly' | 'yearly';

// Map plans to Stripe price IDs via env vars for simplicity
export const priceMap: Record<PlanKey, Record<BillingCycle, string>> = {
  individual: {
    monthly: process.env.STRIPE_PRICE_INDIVIDUAL_MONTHLY || '',
    yearly: process.env.STRIPE_PRICE_INDIVIDUAL_YEARLY || '',
  },
  team: {
    monthly: process.env.STRIPE_PRICE_TEAM_MONTHLY || '',
    yearly: process.env.STRIPE_PRICE_TEAM_YEARLY || '',
  },
};

export function getPriceId(plan: PlanKey, cycle: BillingCycle): string {
  const id = priceMap[plan]?.[cycle];
  if (!id) throw new Error(`Missing Stripe price ID for ${plan}/${cycle}`);
  return id;
}


