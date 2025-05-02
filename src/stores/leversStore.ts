import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { levers as leversData } from 'utils/leversData';
import { ExamplePathways } from 'utils/examplePathways';
import { modelService } from 'services/modelService';
import { AxiosError } from 'axios';

interface ModelResults {
  [key: string]: string | number | object;
}

function getDefaultLeverValue(leverCode: string): number {
  const lever = leversData.find((l) => l.code === leverCode);

  if (!lever) {
    console.error(`Lever with code ${leverCode} not found`);
    return 0;
  }

  lever.range = lever.range || [];

  if (lever.type === 'num') {
    return Math.min(...lever.range.filter((v) => typeof v === 'number'));
  } else {
    // For character levers, return the index 1
    return 1;
  }
}

export const useLeverStore = defineStore('lever', () => {
  // All lever values are now stored as numbers
  const levers = ref<Record<string, number>>({});
  const selectedPathway = ref<string | null>(null);
  const customPathwayName = ref('Custom Pathway');

  const modelResults = ref<ModelResults | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  const getLeverValue = (leverCode: string): number => {
    return levers.value[leverCode] ?? getDefaultLeverValue(leverCode);
  };

  const getAllLeverValues = computed(() => {
    return leversData.map((lever) => levers.value[lever.code] ?? getDefaultLeverValue(lever.code));
  });

  const leversByHeadline = computed(() => {
    const result: Record<string, typeof leversData> = {};

    leversData.forEach((lever) => {
      if (!result[lever.headline]) {
        result[lever.headline] = [];
      }
      result[lever.headline]?.push(lever);
    });

    return result;
  });

  const leversByGroup = computed(() => {
    const result: Record<string, typeof leversData> = {};

    leversData.forEach((lever) => {
      if (!result[lever.group]) {
        result[lever.group] = [];
      } else result[lever.group]?.push(lever);
    });

    return result;
  });

  const isCustomPathway = computed(() => {
    if (!selectedPathway.value) return true;

    const pathwayIndex = ExamplePathways.findIndex(
      (pathway) => pathway.title === selectedPathway.value,
    );

    if (pathwayIndex === -1) return true;

    const pathwayValues = ExamplePathways[pathwayIndex]?.values as number[];
    const currentValues = leversData
      .map((lever, index) => {
        const value = levers.value[lever.code] ?? getDefaultLeverValue(lever.code);
        return index < pathwayValues.length ? value : null;
      })
      .filter((v) => v !== null);

    for (let i = 0; i < currentValues.length; i++) {
      if (currentValues[i] !== pathwayValues[i]) {
        return true;
      }
    }

    return false;
  });

  function setLeverValue(leverCode: string, value: number) {
    const lever = leversData.find((l) => l.code === leverCode);

    if (!lever) {
      console.error(`Lever with code ${leverCode} not found`);
      return;
    }

    if (lever.type === 'num') {
      const range = lever.range.filter((v) => typeof v === 'number');
      if (value < Math.min(...range) || value > Math.max(...range)) {
        console.error(`Value ${value} out of range for lever ${leverCode}`);
        return;
      }
    } else if (lever.type === 'char') {
      // For character levers, check if index is valid, + 1 because [1,2,3] => [A,B,C]
      if (value < 1 || value > lever.range.length + 1) {
        console.error(`Index ${value} out of range for lever ${leverCode}`);
        return;
      }
    }

    levers.value[leverCode] = value;

    if (selectedPathway.value && isCustomPathway.value) {
      selectedPathway.value = null;
    }
  }

  function applyPathway(pathwayTitle: string) {
    const pathway = ExamplePathways.find((p) => p.title === pathwayTitle);

    if (!pathway) {
      console.error(`Pathway "${pathwayTitle}" not found`);
      return;
    }

    levers.value = {};

    leversData.forEach((lever, index) => {
      if (index < pathway.values.length && pathway.values[index]) {
        levers.value[lever.code] = pathway.values[index];
      }
    });

    selectedPathway.value = pathwayTitle;
  }

  function resetToDefaults() {
    levers.value = {};
    selectedPathway.value = null;
  }

  function setCustomPathwayName(name: string) {
    customPathwayName.value = name;
  }

  async function runModel() {
    try {
      isLoading.value = true;
      error.value = null;

      // Get all lever values as a flat array
      const leverValues = leversData.map((lever) => {
        const value = levers.value[lever.code] ?? getDefaultLeverValue(lever.code);

        // For model service, we always send numbers
        return Math.round(value);
      });

      // Convert to string format expected by API
      const leverString = leverValues.join('');

      // Use the API service
      const response = await modelService.runModel(leverString);

      // Check if the response contains an error status
      if (response.data && response.data.status === 'error') {
        error.value = response.data.message || 'An error occurred in the model';
        return null;
      }

      modelResults.value = response.data;
      return response.data;
    } catch (err) {
      console.error('Error running model:', err);
      if (err instanceof AxiosError) {
        if (err.response && err.response.data) {
          if (err.response.data.message) {
            error.value = err.response.data.message;
          } else {
            error.value = `Server error (${err.response.status}): ${err.response.statusText}`;
          }
        } else if (err.request) {
          // Request was made but no response received
          error.value = 'No response from server. Please check if the API server is running.';
        }
      } else if (err instanceof Error) {
        // Something happened in setting up the request
        error.value = err.message || 'Unknown error occurred';
      } else {
        // Handle any other types of errors
        error.value = 'An unknown error occurred';
      }

      throw err;
    } finally {
      isLoading.value = false;
    }
  }

  return {
    levers,
    selectedPathway,
    customPathwayName,

    getLeverValue,
    getAllLeverValues,
    leversByHeadline,
    leversByGroup,
    isCustomPathway,

    modelResults,
    isLoading,
    error,
    runModel,

    setLeverValue,
    applyPathway,
    resetToDefaults,
    setCustomPathwayName,
  };
});
