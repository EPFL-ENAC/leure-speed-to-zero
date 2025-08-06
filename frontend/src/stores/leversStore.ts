import { defineStore } from 'pinia';
import { computed, ref, watch } from 'vue';
import type { Lever } from 'utils/leversData';
import { levers as leversData } from 'utils/leversData';
import { ExamplePathways } from 'utils/examplePathways';
import { modelService } from 'services/modelService';
import { AxiosError } from 'axios';
import type { Region } from 'src/utils/region';

// Types
export interface YearData {
  year: number;
  [key: string]: number;
}

export interface SectorData {
  countries: {
    [key in Region]: YearData[];
  };
  units: {
    [key: string]: string;
  };
}

export interface ModelResults {
  fingerprint_result: string;
  fingerprint_input: string;
  status: string;
  sectors: string[];
  data: {
    climate: SectorData;
    lifestyles: SectorData;
    transport: SectorData;
    buildings: SectorData;
    forestry: SectorData;
    agriculture: SectorData;
  };
}

// Helper functions moved outside the store
function getDefaultLeverValue(leverCode: string): number {
  const lever = leversData.find((l) => l.code === leverCode);
  if (!lever) return 0;

  lever.range = lever.range || [];

  if (lever.type === 'num') {
    return Math.min(...lever.range.filter((v) => typeof v === 'number'));
  } else {
    return 1; // For character levers, return the index 1
  }
}

export const useLeverStore = defineStore('lever', () => {
  // State
  const levers = ref<Record<string, number>>({});
  const selectedPathway = ref<string | null>(null);
  const customPathwayName = ref('Custom Pathway');
  const modelResults = ref<ModelResults | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const autoRun = ref(true);

  // Private variables (not exposed in the return)
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;
  const debounceDelay = 500;

  // Computed values
  const getLeverValue = (leverCode: string): number =>
    levers.value[leverCode] ?? getDefaultLeverValue(leverCode);

  const getAllLeverValues = computed(() =>
    leversData.map((lever) => levers.value[lever.code] ?? getDefaultLeverValue(lever.code)),
  );

  const leversByHeadline = computed(() => {
    const result: Record<string, typeof leversData> = {};
    leversData.forEach((lever) => {
      if (!result[lever.headline]) result[lever.headline] = [];
      result[lever.headline]?.push(lever);
    });
    return result;
  });

  const leversByGroup = computed(() => {
    const result: Record<string, typeof leversData> = {};
    leversData.forEach((lever) => {
      if (!result[lever.group]) result[lever.group] = [];
      result[lever.group]?.push(lever);
    });
    return result;
  });

  const isCustomPathway = computed(() => {
    if (!selectedPathway.value) return true;

    const pathway = ExamplePathways.find((p) => p.title === selectedPathway.value);
    if (!pathway) return true;

    return leversData.some((lever) => {
      const currentValue = levers.value[lever.code] ?? getDefaultLeverValue(lever.code);
      return pathway.values[lever.code] && currentValue !== pathway.values[lever.code];
    });
  });

  // Sectors computed values
  const buildings = computed(() => {
    if (!modelResults.value) return null;
    return modelResults.value.data.buildings;
  });

  const transport = computed(() => {
    if (!modelResults.value) return null;
    return modelResults.value.data.transport;
  });

  const forestry = computed(() => {
    if (!modelResults.value) return null;
    return modelResults.value.data.forestry;
  });

  const agriculture = computed(() => {
    if (!modelResults.value) return null;
    return modelResults.value.data.agriculture;
  });

  // Model operations
  let lastRunTime = 0;

  function debouncedRunModel() {
    if (!autoRun.value) return;

    // Clear existing timer if there is one
    if (debounceTimer) clearTimeout(debounceTimer);

    const now = Date.now();
    const timeElapsed = now - lastRunTime;

    // If we recently ran the model, schedule a delayed run
    if (timeElapsed < debounceDelay) {
      debounceTimer = setTimeout(() => {
        lastRunTime = Date.now();
        debounceTimer = null;
        runModel().catch((err) => console.error('Auto-run model failed:', err));
      }, debounceDelay);
    } else {
      // Otherwise run immediately
      lastRunTime = now;
      runModel().catch((err) => console.error('Auto-run model failed:', err));
    }
  }

  async function runModel() {
    try {
      isLoading.value = true;
      error.value = null;

      // Get all lever values as a flat array
      const leverValues = leversData.map((lever) =>
        Math.round(levers.value[lever.code] ?? getDefaultLeverValue(lever.code)),
      );

      // Convert to string format expected by API
      const leverString = leverValues.join('');

      // Use the API service
      const response = await modelService.runModel(leverString);
      console.log('Running model with lever string:', leverString);
      // Handle error status from API
      if (response.data?.status === 'error') {
        error.value = response.data.message || 'An error occurred in the model';
        return null;
      }

      modelResults.value = response.data;
      return response.data;
    } catch (err) {
      handleModelError(err);
      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  // Error handling extracted to a separate function
  function handleModelError(err: unknown) {
    console.error('Error running model:', err);

    if (err instanceof AxiosError) {
      if (err.response?.data?.message) {
        error.value = err.response.data.message;
      } else if (err.response) {
        error.value = `Server error (${err.response.status}): ${err.response.statusText}`;
      } else if (err.request) {
        error.value = 'No response from server. Please check if the API server is running.';
      }
    } else if (err instanceof Error) {
      error.value = err.message || 'Unknown error occurred';
    } else {
      error.value = 'An unknown error occurred';
    }
  }

  // Lever operations
  function setLeverValue(leverCode: string, value: number) {
    const lever = leversData.find((l) => l.code === leverCode);
    if (!lever || !isValidLeverValue(lever, value)) return;

    levers.value[leverCode] = value;
  }

  function batchUpdateLevers(updates: Record<string, number>) {
    // Create a new object combining current state with updates
    const newLevers = { ...levers.value };

    // Process all updates
    Object.entries(updates).forEach(([leverCode, value]) => {
      const lever = leversData.find((l) => l.code === leverCode);
      if (lever && isValidLeverValue(lever, value)) {
        newLevers[leverCode] = value;
      }
    });

    // Update the state in a single operation
    levers.value = newLevers;
  }

  function isValidLeverValue(lever: Lever, value: number): boolean {
    if (lever.type === 'num') {
      const range = lever.range.filter((v) => typeof v === 'number');
      if (value < Math.min(...range) || value > Math.max(...range)) {
        console.error(`Value ${value} out of range for lever ${lever.code}`);
        return false;
      }
    } else if (lever.type === 'char') {
      if (value < 1 || value > lever.range.length) {
        console.error(`Index ${value} out of range for lever ${lever.code}`);
        return false;
      }
    }
    return true;
  }

  // Pathway operations
  function applyPathway(pathwayTitle: string) {
    const pathway = ExamplePathways.find((p) => p.title === pathwayTitle);
    if (!pathway) {
      console.error(`Pathway "${pathwayTitle}" not found`);
      return;
    }

    const updates: Record<string, number> = {};

    // Add all lever updates to the batch
    leversData.forEach((lever) => {
      if (pathway.values[lever.code]) {
        updates[lever.code] = pathway.values[lever.code] as number;
      }
    });

    // Flag that we're doing a batch update

    levers.value = updates;
    selectedPathway.value = pathwayTitle;
  }

  function resetToDefaults() {
    // Reset state
    levers.value = {};
    selectedPathway.value = null;
  }

  // Watchers
  watch(
    levers,
    () => {
      // Handle pathway selection
      if (selectedPathway.value && isCustomPathway.value) {
        selectedPathway.value = null;
      }

      // Run the model
      debouncedRunModel();
    },
    { deep: true, immediate: true },
  );

  // Store interface
  return {
    // State
    levers,
    selectedPathway,
    customPathwayName,
    autoRun,
    modelResults,
    isLoading,
    error,

    // Getters
    getLeverValue,
    getAllLeverValues,
    leversByHeadline,
    leversByGroup,
    isCustomPathway,

    buildings,
    transport,
    forestry,
    agriculture,

    // Actions
    batchUpdateLevers,
    runModel,
    setLeverValue,
    applyPathway,
    resetToDefaults,
    setCustomPathwayName: (name: string) => {
      customPathwayName.value = name;
    },
    toggleAutoRun: () => {
      autoRun.value = !autoRun.value;
      if (autoRun.value) {
        runModel().catch((err) =>
          console.error('Error running model after enabling auto-run:', err),
        );
      }
    },
  };
});
