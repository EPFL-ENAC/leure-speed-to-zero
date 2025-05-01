import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { levers as leversData } from '@/utils/leversData';
import { ExamplePathways } from '@/utils/examplePathways';
import { modelService } from '@/services/modelService';

interface ModelResults {
  [key: string]: string | number | object;
}

function getDefaultLeverValue(leverCode: string): number | string {
  const lever = leversData.find((l) => l.code === leverCode);

  if (!lever) {
    console.error(`Lever with code ${leverCode} not found`);
    return 0;
  } else {
    lever.range = lever.range || [];
    return lever.type === 'num' ? Math.min(...(lever.range as number[])) : (lever.range[0] ?? '');
  }
}

export const useLeverStore = defineStore('lever', () => {
  const levers = ref<Record<string, number | string>>({});
  const selectedPathway = ref<string | null>(null);
  const customPathwayName = ref('Custom Pathway');

  const modelResults = ref<ModelResults | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  const getLeverValue = (leverCode: string) => {
    return levers.value[leverCode] || getDefaultLeverValue(leverCode);
  };

  const getAllLeverValues = computed(() => {
    return leversData.map((lever) => levers.value[lever.code] || getDefaultLeverValue(lever.code));
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
        const value = levers.value[lever.code] || getDefaultLeverValue(lever.code);
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

  function setLeverValue(leverCode: string, value: number | string) {
    const lever = leversData.find((l) => l.code === leverCode);

    if (!lever) {
      console.error(`Lever with code ${leverCode} not found`);
      return;
    }

    if (lever.type === 'num') {
      const numValue = value as number;
      const range = lever.range as number[];

      if (numValue < Math.min(...range) || numValue > Math.max(...range)) {
        console.error(`Value ${value} out of range for lever ${leverCode}`);
        return;
      }
    } else if (lever.type === 'char') {
      const charValue = value as string;
      const range = lever.range as string[];

      if (!range.includes(charValue)) {
        console.error(`Value ${value} not allowed for lever ${leverCode}`);
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
      const leverValues = leversData.map(
        (lever) => levers.value[lever.code] || getDefaultLeverValue(lever.code),
      );

      // Convert to string format expected by API
      const leverString = leverValues.join('');

      // Use the API service
      const response = await modelService.runModel(leverString);
      modelResults.value = response.data;
      return response.data;
    } catch (err) {
      console.error('Error running model:', err);
      error.value = err instanceof Error ? err.message : 'Unknown error occurred';
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
