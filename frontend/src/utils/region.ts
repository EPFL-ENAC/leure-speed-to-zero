import sharedConfig from '../../model_config.json';

export const REGION_CONFIG = {
  // Use environment variable with fallback
  MODEL_PRIMARY_REGION: sharedConfig.MODEL_PRIMARY_REGION || 'Vaud',

  AVAILABLE_REGIONS: sharedConfig.AVAILABLE_REGIONS,
} as const;

// Type for available regions
export type Region = (typeof REGION_CONFIG.AVAILABLE_REGIONS)[number];

// Helper functions
export const getCurrentRegion = (): Region => REGION_CONFIG.MODEL_PRIMARY_REGION;
