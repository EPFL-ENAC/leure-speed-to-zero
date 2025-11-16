import { ref } from 'vue';
import axios from 'axios';

// Runtime region configuration
interface RegionConfig {
  current_region: string;
  available_regions: string[];
}

// Default configuration (fallback)
const DEFAULT_CONFIG: RegionConfig = {
  current_region: 'Vaud',
  available_regions: ['Vaud', 'Switzerland', 'EU27'],
};

// Reactive state for region configuration
const regionConfig = ref<RegionConfig>(DEFAULT_CONFIG);
const isLoaded = ref(false);
const isLoading = ref(false);

// Fetch region configuration from backend
export async function loadRegionConfig(): Promise<void> {
  if (isLoaded.value || isLoading.value) return;

  isLoading.value = true;
  try {
    const response = await axios.get<{
      status: string;
      current_region: string;
      available_regions: string[];
    }>('/api/debug-region');

    if (response.data.status === 'success') {
      regionConfig.value = {
        current_region: response.data.current_region,
        available_regions: response.data.available_regions,
      };
      isLoaded.value = true;
    }
  } catch (error) {
    console.warn('Failed to load region config from backend, using defaults:', error);
    // Keep using DEFAULT_CONFIG on error
  } finally {
    isLoading.value = false;
  }
}

// Type for available regions
export type Region = string;

// Helper functions
export const getCurrentRegion = (): Region => regionConfig.value.current_region;
export const getAvailableRegions = (): Region[] => regionConfig.value.available_regions;
export const isRegionConfigLoaded = () => isLoaded.value;
