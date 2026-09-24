import { ref } from 'vue';
import axios from 'axios';

// Runtime configuration of this deployment, read from the backend at startup.
// One image serves several sites: the profile says which region, which sectors
// and which levers this one has.
interface AppConfig {
  profile: string;
  title: string | null;
  logo: string | null;
  current_region: string;
  available_regions: string[];
  sectors: string[];
  lever_keys: string[];
}

// Default configuration (fallback)
const DEFAULT_CONFIG: AppConfig = {
  profile: 'default',
  title: null,
  logo: null,
  current_region: 'Vaud',
  available_regions: ['Vaud', 'Switzerland', 'EU27'],
  sectors: [],
  lever_keys: [],
};

// Reactive state for the app configuration
const appConfig = ref<AppConfig>(DEFAULT_CONFIG);
const isLoaded = ref(false);
const isLoading = ref(false);

// Fetch the configuration from the backend
export async function loadRegionConfig(): Promise<void> {
  if (isLoaded.value || isLoading.value) return;

  isLoading.value = true;
  try {
    const response = await axios.get<AppConfig & { status: string }>('/api/v1/app-config');

    if (response.data.status === 'success') {
      appConfig.value = {
        profile: response.data.profile || 'default',
        title: response.data.title ?? null,
        logo: response.data.logo ?? null,
        current_region: response.data.current_region,
        available_regions: response.data.available_regions,
        sectors: response.data.sectors ?? [],
        lever_keys: response.data.lever_keys ?? [],
      };
      isLoaded.value = true;
      if (appConfig.value.title) {
        document.title = appConfig.value.title;
      }
    }
  } catch (error) {
    console.warn('Failed to load app config from backend, using defaults:', error);
    // Keep using DEFAULT_CONFIG on error
  } finally {
    isLoading.value = false;
  }
}

// Type for available regions
export type Region = string;

// Helper functions
export const getCurrentRegion = (): Region => appConfig.value.current_region;
export const getAvailableRegions = (): Region[] => appConfig.value.available_regions;
export const isRegionConfigLoaded = () => isLoaded.value;

// Profile helpers. An empty sector list means "no profile", show everything.
export const getProfile = (): string => appConfig.value.profile;
export const getProfileTitle = (): string | null => appConfig.value.title;
export const getProfileLogo = (): string | null => appConfig.value.logo;
export const getProfileSectors = (): string[] => appConfig.value.sectors;
export const getLeverKeys = (): string[] => appConfig.value.lever_keys;
