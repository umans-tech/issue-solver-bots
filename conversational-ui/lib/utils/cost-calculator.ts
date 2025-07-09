/**
 * Cost calculation utility for LLM providers
 * 
 * This utility provides pricing information and cost calculation for various LLM providers
 * including OpenAI and Anthropic models.
 */

// Pricing data structure
interface ModelPricing {
  inputTokenPrice: number;  // per token
  outputTokenPrice: number; // per token
}

interface ProviderPricing {
  [model: string]: ModelPricing;
}

// OpenAI Pricing (as of 2024 - prices per 1M tokens)
const OPENAI_PRICING: ProviderPricing = {
  'gpt-4.1-mini': {
    inputTokenPrice: 0.00015 / 1000, // $0.15 per 1M tokens
    outputTokenPrice: 0.0006 / 1000,  // $0.60 per 1M tokens
  },
  'gpt-4.1': {
    inputTokenPrice: 0.015 / 1000,    // $15 per 1M tokens
    outputTokenPrice: 0.03 / 1000,    // $30 per 1M tokens
  },
  'gpt-4o': {
    inputTokenPrice: 0.0025 / 1000,   // $2.50 per 1M tokens
    outputTokenPrice: 0.01 / 1000,    // $10 per 1M tokens
  },
  'gpt-4o-mini': {
    inputTokenPrice: 0.00015 / 1000,  // $0.15 per 1M tokens
    outputTokenPrice: 0.0006 / 1000,  // $0.60 per 1M tokens
  },
  'o3-mini': {
    inputTokenPrice: 0.0025 / 1000,   // $2.50 per 1M tokens
    outputTokenPrice: 0.01 / 1000,    // $10 per 1M tokens
  },
  'dall-e-2': {
    inputTokenPrice: 0.02,            // $0.02 per image
    outputTokenPrice: 0,              // No output token cost
  },
  'dall-e-3': {
    inputTokenPrice: 0.04,            // $0.04 per image
    outputTokenPrice: 0,              // No output token cost
  },
};

// Anthropic Pricing (as of 2024 - prices per 1M tokens)
const ANTHROPIC_PRICING: ProviderPricing = {
  'claude-3-5-sonnet-latest': {
    inputTokenPrice: 0.003 / 1000,    // $3 per 1M tokens
    outputTokenPrice: 0.015 / 1000,   // $15 per 1M tokens
  },
  'claude-3-7-sonnet-latest': {
    inputTokenPrice: 0.003 / 1000,    // $3 per 1M tokens
    outputTokenPrice: 0.015 / 1000,   // $15 per 1M tokens
  },
  'claude-sonnet-4-20250514': {
    inputTokenPrice: 0.015 / 1000,    // $15 per 1M tokens
    outputTokenPrice: 0.075 / 1000,   // $75 per 1M tokens
  },
  'claude-opus-4-20250514': {
    inputTokenPrice: 0.075 / 1000,    // $75 per 1M tokens
    outputTokenPrice: 0.375 / 1000,   // $375 per 1M tokens
  },
};

// Provider lookup
const PROVIDER_PRICING = {
  openai: OPENAI_PRICING,
  anthropic: ANTHROPIC_PRICING,
};

/**
 * Calculate the cost for a given model and token usage
 * @param provider - The LLM provider ('openai' or 'anthropic')
 * @param model - The model name
 * @param inputTokens - Number of input tokens
 * @param outputTokens - Number of output tokens
 * @returns Cost in USD
 */
export function calculateCost(
  provider: 'openai' | 'anthropic',
  model: string,
  inputTokens: number,
  outputTokens: number
): number {
  const providerPricing = PROVIDER_PRICING[provider];
  if (!providerPricing) {
    console.warn(`Unknown provider: ${provider}`);
    return 0;
  }

  const modelPricing = providerPricing[model];
  if (!modelPricing) {
    console.warn(`Unknown model for ${provider}: ${model}`);
    return 0;
  }

  const inputCost = inputTokens * modelPricing.inputTokenPrice;
  const outputCost = outputTokens * modelPricing.outputTokenPrice;
  
  return inputCost + outputCost;
}

/**
 * Get the pricing information for a model
 * @param provider - The LLM provider
 * @param model - The model name
 * @returns Pricing information or null if not found
 */
export function getModelPricing(
  provider: 'openai' | 'anthropic',
  model: string
): ModelPricing | null {
  const providerPricing = PROVIDER_PRICING[provider];
  if (!providerPricing) {
    return null;
  }

  return providerPricing[model] || null;
}

/**
 * Get all available models for a provider
 * @param provider - The LLM provider
 * @returns Array of model names
 */
export function getAvailableModels(provider: 'openai' | 'anthropic'): string[] {
  const providerPricing = PROVIDER_PRICING[provider];
  if (!providerPricing) {
    return [];
  }

  return Object.keys(providerPricing);
}

/**
 * Format cost as a currency string
 * @param cost - Cost in USD
 * @param decimals - Number of decimal places (default: 6)
 * @returns Formatted cost string
 */
export function formatCost(cost: number, decimals: number = 6): string {
  return `$${cost.toFixed(decimals)}`;
}