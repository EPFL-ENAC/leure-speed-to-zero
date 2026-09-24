import { defineStore } from 'pinia';
import { computed, ref, watch } from 'vue';
import type { Lever } from 'utils/leversData';
import { levers as leversData } from 'utils/leversData';
import { sectors } from 'utils/sectors';
import { ExamplePathways, type PathWay } from 'utils/examplePathways';
import { modelService } from 'services/modelService';
import { AxiosError } from 'axios';
import { getCurrentRegion, getLeverKeys, type Region } from 'src/utils/region';
import type { KpiData } from 'src/utils/sectors';
import { getTranslatedText, type TranslationObject } from 'src/utils/translationHelpers';
import { useI18n } from 'vue-i18n';
import { withSelfSufficiencyMetrics } from 'src/utils/selfSufficiency';
import { withLivestockMetrics } from 'src/utils/livestockMetrics';
import {
  ORGANIC_SHARE_LEVERS,
  withOrganicShares,
  type LeverSeriesRow,
  type OrganicShareRows,
} from 'src/utils/organicShares';
import { withDietMetrics, type EnergyRequirementRow } from 'src/utils/dietMetrics';
import { withPopulationMetrics } from 'src/utils/populationMetrics';
import { withTrueCostPerCapita, withTrueCostSavings } from 'src/utils/trueCostMetrics';
import {
  COMPARISON_PATHWAYS,
  buildPathwayRuns,
  type PathwayRun,
} from 'src/utils/pathwayComparison';

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

export interface OutputConfig {
  id: string;
  color?: string;
}

export interface ChartConfig {
  title: string | TranslationObject;
  type: string;
  unit: string;
  outputs: Array<string | OutputConfig>;
  // When set, every plotted value is divided by it, so "unit" can be a multiple
  // of the model's unit (e.g. scale 1e9 with unit "Billion CHF" for CHF outputs).
  scale?: number;
  // When set (as [yearA, yearB, ...]), the chart compares these years side by
  // side as a bar chart (categories, not a time series) instead of plotting
  // the full trajectory.
  snapshotYears?: number[];
  snapshotLabels?: Array<string | TranslationObject>;
  // When set, sums the listed outputs into one series per group instead of one
  // series per output - keeps a long category list readable in a snapshot chart.
  groups?: Record<string, { label: string | TranslationObject; color?: string; outputs: string[] }>;
}

export interface SectorWithKpis extends SectorData {
  kpis: KpiData[];
}

export type SectorKey = string;

// Sentinel "year" for the synthetic BAU (2050) row appended to the merged
// dietary-habits data (see getSectorDataWithKpis). Chart components must
// exclude it from any time-series (non-snapshot) rendering.
export const BAU_2050_SNAPSHOT_YEAR = 99999;

export interface LeverYearData {
  Country: string;
  Years: number;
  [key: string]: string | number;
}

export interface LeverMetadata {
  countries: string[];
  years: number[];
  variables: string[];
  units: {
    [key: string]: string;
  };
}

export interface LeverResults {
  status: string;
  lever_name: string;
  country: string;
  modules: string[];
  data: {
    lever_positions: {
      [key: number]: LeverYearData[];
    };
    metadata: LeverMetadata;
  };
}

export interface ModelResults {
  fingerprint_result: string;
  fingerprint_input: string;
  status: string;
  sectors: string[];
  data: {
    [sector: string]: SectorData;
  };
  kpis: {
    [sector: string]: KpiData[];
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
  // Composables
  const { locale } = useI18n();

  // State
  const levers = ref<Record<string, number>>({});
  const selectedPathway = ref<string | null>(null);
  const customPathwayName = ref('Custom Pathway');
  const modelResults = ref<ModelResults | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const autoRun = ref(true);
  const leverData = ref<LeverResults | null>(null);
  const currentSector = ref<string | null>(null);

  // Private variables (not exposed in the return)
  let debounceTimer: ReturnType<typeof setTimeout> | null = null;
  const debounceDelay = 10;

  const getLeverValue = (leverCode: string): number =>
    levers.value[leverCode] ?? getDefaultLeverValue(leverCode);

  const getAllLeverValues = computed(() =>
    leversData.map((lever) => levers.value[lever.code] ?? getDefaultLeverValue(lever.code)),
  );

  const leversByHeadline = computed(() => {
    const result: Record<string, Lever[]> = {};
    leversData.forEach((lever) => {
      const headlineKey = getTranslatedText(lever.headline, locale.value);
      if (!result[headlineKey]) result[headlineKey] = [];
      result[headlineKey]?.push(lever);
    });
    return result;
  });

  // Function to get levers filtered by sector (with translations)
  const getLeversForSector = (sectorCode: string): Lever[] => {
    // Find the sector configuration
    const sector = sectors.find((s) => s.value === sectorCode);
    if (!sector) return [];

    // Keep only the levers the loaded model knows: a sector may list levers
    // a given model build does not have.
    const known = getLeverKeys();
    const sectorLevers = sector.levers
      .filter((leverId) => known.length === 0 || known.includes(leverId))
      .map((leverId) => leversData.find((l) => l.code === leverId))
      .filter((lever): lever is Lever => lever !== undefined);

    return sectorLevers;
  };

  const leversByGroup = computed(() => {
    const result: Record<string, Lever[]> = {};
    leversData.forEach((lever) => {
      const groupKey = getTranslatedText(lever.group, locale.value);
      if (!result[groupKey]) result[groupKey] = [];
      result[groupKey]?.push(lever);
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

  // Merges every sector's country data into one object, keyed by output name.
  function mergeAllSectorData(): { countries: { [key: string]: YearData[] }; kpis: KpiData[] } {
    const allSectorData = modelResults.value?.data || {};
    const countries: { [key: string]: YearData[] } = {};

    Object.values(allSectorData).forEach((sectorData) => {
      if (sectorData.countries) {
        Object.entries(sectorData.countries).forEach(([country, yearDataArray]) => {
          if (!countries[country]) {
            // Initialize with the year structure from the first sector
            countries[country] = yearDataArray.map((yd) => ({ year: yd.year }));
          }

          // Merge outputs from this sector into each year's data
          yearDataArray.forEach((yearData, index) => {
            if (countries[country]?.[index]) {
              Object.assign(countries[country][index], yearData);
            }
          });
        });
      }
    });

    const allKpis = Object.values(modelResults.value?.kpis || {}).flat();

    return { countries, kpis: allKpis };
  }

  // Merges a specific list of sectors' country data into one object, aligning
  // rows by position (every TCAF sector shares the same year range/order).
  function mergeSectorsData(sectorDatas: Array<SectorData | undefined>): {
    countries: { [key: string]: YearData[] };
    units: { [key: string]: string };
  } {
    const countries: { [key: string]: YearData[] } = {};
    const units: { [key: string]: string } = {};

    sectorDatas.forEach((sectorData) => {
      if (!sectorData?.countries) return;
      Object.assign(units, sectorData.units);
      Object.entries(sectorData.countries).forEach(([country, yearDataArray]) => {
        if (!countries[country]) {
          countries[country] = yearDataArray.map((yd) => ({ year: yd.year }));
        }
        yearDataArray.forEach((yearData, index) => {
          if (countries[country]?.[index]) {
            Object.assign(countries[country][index], yearData);
          }
        });
      });
    });

    return { countries, units };
  }

  // A fixed "business as usual" diet reference, fetched once (it does not
  // depend on the user's current levers) and used to add a "BAU (2050)" bar
  // to the diet snapshot chart, isolating the diet-policy effect from
  // everything else (population, ...) that also changes between 2023 and 2050.
  // The same run, every module merged, is the baseline the True Cost page
  // measures its savings against.
  const bauReferenceSectorData = ref<SectorData | null>(null);
  const bauReferenceAllSectorData = ref<SectorData | null>(null);
  let bauReferenceLoading = false;

  // Runs the model for a pathway's lever values (whatever the user's levers are
  // now) and returns the results of every sector, or null when the run failed.
  // Every TCAF page's sectors are covered by the "dietary-habits" run.
  async function runPathwayModel(pathway: PathWay): Promise<ModelResults['data'] | null> {
    const modelKeys = getLeverKeys();
    const order = modelKeys.length > 0 ? modelKeys : leversData.map((l) => l.code);
    const leverValues = order.map((code) =>
      Math.round(pathway.values[code] ?? getDefaultLeverValue(code)),
    );
    const response = await modelService.runModel(leverValues.join(''), 'dietary-habits');
    if (response.data?.status === 'error') return null;
    return response.data?.data ?? null;
  }

  async function ensureBauReference() {
    if (bauReferenceSectorData.value || bauReferenceLoading) return;
    const pathway = ExamplePathways.find((p) => p.title === 'Business as usual (diet)');
    if (!pathway) return;

    bauReferenceLoading = true;
    try {
      const data = await runPathwayModel(pathway);
      if (data) {
        // Population rides along so the synthetic BAU (2050) row can be
        // converted to a per-capita value like the other snapshot rows.
        bauReferenceSectorData.value = data['dietary-habits']
          ? mergeSectorsData([data['population'], data['dietary-habits']])
          : null;
        bauReferenceAllSectorData.value = mergeSectorsData(Object.values(data));
      }
    } catch (err) {
      console.error('Failed to fetch the BAU reference scenario:', err);
    } finally {
      bauReferenceLoading = false;
    }
  }

  // The Pathway comparison page charts the six TCAF diet pathways side by side,
  // so it needs a run of each, all fixed (none depends on the user's levers):
  // fetched once, in parallel, and kept by pathway title. The backend caches each
  // run, and the BAU one is the run the reference above already made.
  const pathwayComparisonResults = ref<Record<string, SectorData>>({});
  const pathwayComparisonLoading = ref(false);
  const pathwayComparisonError = ref<string | null>(null);

  const pathwayComparisonProgress = computed(() => ({
    done: Object.keys(pathwayComparisonResults.value).length,
    total: COMPARISON_PATHWAYS.length,
  }));

  const pathwayComparison = computed<PathwayRun[]>(() =>
    buildPathwayRuns(pathwayComparisonResults.value, getCurrentRegion()),
  );

  async function ensurePathwayComparison() {
    if (pathwayComparisonLoading.value) return;

    const missing = COMPARISON_PATHWAYS.filter(
      (cp) =>
        !pathwayComparisonResults.value[cp.title] &&
        ExamplePathways.some((p) => p.title === cp.title),
    );
    if (missing.length === 0) return;

    pathwayComparisonLoading.value = true;
    pathwayComparisonError.value = null;
    try {
      await Promise.all(
        missing.map(async (cp) => {
          const pathway = ExamplePathways.find((p) => p.title === cp.title) as PathWay;
          const data = await runPathwayModel(pathway);
          if (!data) throw new Error(`The model failed to run the "${cp.title}" pathway`);
          // Reassign rather than mutate, so the results (and what is derived from them) update
          pathwayComparisonResults.value = {
            ...pathwayComparisonResults.value,
            [cp.title]: mergeSectorsData(Object.values(data)),
          };
        }),
      );
    } catch (err) {
      console.error('Failed to fetch the pathway comparison runs:', err);
      pathwayComparisonError.value = err instanceof Error ? err.message : String(err);
    } finally {
      pathwayComparisonLoading.value = false;
    }
  }

  // The individual energy requirement by sex and age group is an input of the
  // model (the "kcal-req" lever), not one of its outputs, so the Diet page
  // reads it from the lever-data endpoint: one time series per lever position
  // (1-4), fetched once per region. The selected position is merged into the
  // page's rows (see withDietMetrics).
  const ENERGY_REQUIREMENT_LEVER = 'lever_kcal-req';
  const energyRequirement = ref<Record<string, Record<string, EnergyRequirementRow[]>>>({});
  const energyRequirementLoading = new Set<string>();

  async function ensureEnergyRequirement(region: string) {
    if (energyRequirement.value[region] || energyRequirementLoading.has(region)) return;

    energyRequirementLoading.add(region);
    try {
      const response = await modelService.getLeverData(ENERGY_REQUIREMENT_LEVER, undefined, region);
      const positions = response.data?.data?.lever_positions;
      if (response.data?.status === 'success' && positions) {
        energyRequirement.value = { ...energyRequirement.value, [region]: positions };
      }
    } catch (err) {
      console.error('Failed to fetch the energy requirement:', err);
    } finally {
      energyRequirementLoading.delete(region);
    }
  }

  // The organic shares of the Production page are the model's
  // "crop-share-organic" and "share-organic" lever inputs, not outputs: one time
  // series per lever position (1-4), fetched once per lever and region. The
  // selected positions are merged into the page's rows (see withOrganicShares).
  const organicShareSeries = ref<Record<string, Record<string, Record<string, LeverSeriesRow[]>>>>(
    {},
  );
  const organicShareLoading = new Set<string>();

  async function ensureOrganicShares(region: string) {
    await Promise.all(
      ORGANIC_SHARE_LEVERS.map(async (lever) => {
        const key = `${lever}|${region}`;
        if (organicShareSeries.value[lever]?.[region] || organicShareLoading.has(key)) return;

        organicShareLoading.add(key);
        try {
          const response = await modelService.getLeverData(lever, undefined, region);
          const positions = response.data?.data?.lever_positions;
          if (response.data?.status === 'success' && positions) {
            organicShareSeries.value = {
              ...organicShareSeries.value,
              [lever]: { ...organicShareSeries.value[lever], [region]: positions },
            };
          }
        } catch (err) {
          console.error(`Failed to fetch ${lever}:`, err);
        } finally {
          organicShareLoading.delete(key);
        }
      }),
    );
  }

  function selectedOrganicShares(region: string): OrganicShareRows | undefined {
    const rows: Record<string, LeverSeriesRow[]> = {};
    ORGANIC_SHARE_LEVERS.forEach((lever) => {
      const position = String(Math.round(getLeverValue(lever)));
      const leverRows = organicShareSeries.value[lever]?.[region]?.[position];
      if (leverRows) rows[lever] = leverRows;
    });
    return Object.keys(rows).length ? { region, rows } : undefined;
  }

  // Sectors computed values
  const getSectorDataWithKpis = (sectorName: string): SectorWithKpis | null => {
    if (!modelResults.value) return null;

    // Special case: the Production tab needs demand (from "dietary-habits",
    // which reacts to the diet-composition levers) and domestic production
    // (from "crop" and "livestock", which react to the self-sufficiency
    // levers) together, to add the derived import/export/self-sufficiency
    // fields it charts, the livestock productivity of its Livestock sub-tab
    // the cropland area and yield ("land-use") of its Crops one, the Swiss
    // fish production and its cost ("TCAF") of its Blue food one, and the
    // organic shares (lever inputs) of both. The
    // "agriculture" module is a legacy computation that ignores
    // every TCAF lever, so it must never be used as a data source here.
    if (sectorName === 'production') {
      const demandSector = modelResults.value.data['dietary-habits'];
      if (!demandSector) return null;
      const merged = mergeSectorsData([
        demandSector,
        modelResults.value.data['crop'],
        modelResults.value.data['livestock'],
        modelResults.value.data['land-use'],
        modelResults.value.data['TCAF'],
      ]);
      const kpis = modelResults.value.kpis['crop'] || [];
      const region = getCurrentRegion();
      void ensureOrganicShares(region);
      return {
        countries: withOrganicShares(
          withLivestockMetrics(withSelfSufficiencyMetrics(merged.countries)),
          selectedOrganicShares(region),
        ) as SectorData['countries'],
        units: merged.units,
        kpis,
      };
    }

    // Special case: the Population page charts the population sector's total
    // and adds the change and growth rate derived from it.
    if (sectorName === 'population') {
      const populationSector = modelResults.value.data['population'];
      if (!populationSector) return null;
      return {
        countries: withPopulationMetrics(populationSector.countries) as SectorData['countries'],
        units: populationSector.units,
        kpis: modelResults.value.kpis['population'] || [],
      };
    }

    // Special case: the Dietary habits page merges every sector like "" does,
    // appends a synthetic BAU (2050) row (year = BAU_2050_SNAPSHOT_YEAR) for its
    // diet snapshot chart, and adds the derived intake / food-waste fields and the
    // energy requirement.
    if (sectorName === 'dietary-habits') {
      void ensureBauReference();
      const merged = mergeAllSectorData();

      const bauCountries = bauReferenceSectorData.value?.countries;
      if (bauCountries) {
        Object.entries(bauCountries).forEach(([region, rows]) => {
          const row2050 = rows.find((r) => Number(r.year) === 2050);
          if (!row2050 || !merged.countries[region]) return;
          merged.countries[region] = [
            ...merged.countries[region],
            { ...row2050, year: BAU_2050_SNAPSHOT_YEAR },
          ];
        });
      }

      const region = getCurrentRegion();
      void ensureEnergyRequirement(region);
      const position = String(Math.round(getLeverValue(ENERGY_REQUIREMENT_LEVER)));
      const requirementRows = energyRequirement.value[region]?.[position];

      return {
        countries: withDietMetrics(
          merged.countries,
          requirementRows && { region, rows: requirementRows },
        ) as SectorData['countries'],
        units: {},
        kpis: merged.kpis,
      };
    }

    // Special case: the True Cost page merges every sector like "" does and adds
    // the cost saved against the BAU (diet) reference run and the costs per capita.
    if (sectorName === 'true-cost') {
      void ensureBauReference();
      const merged = mergeAllSectorData();
      return {
        countries: withTrueCostPerCapita(
          withTrueCostSavings(merged.countries, bauReferenceAllSectorData.value?.countries),
        ) as SectorData['countries'],
        units: {},
        kpis: merged.kpis,
      };
    }

    // Special case: empty sectorName means "overall" - aggregate all sectors
    if (!sectorName || sectorName === '') {
      const merged = mergeAllSectorData();
      return {
        countries: merged.countries,
        units: {}, // Units are merged per-output, not needed at this level
        kpis: merged.kpis,
      };
    }

    const sectorData = modelResults.value.data[sectorName];
    if (!sectorData) return null;
    const kpis = modelResults.value.kpis[sectorName] || [];
    return { ...sectorData, kpis };
  };

  // Model operations
  let lastRunTime = 0;

  // Lever data operations
  async function fetchLeverData(leverName: string, modules?: string, country?: string) {
    try {
      // Use current sector if no modules specified
      const sector = currentSector.value || undefined;
      const response = await modelService.getLeverData(leverName, sector, country);

      // Handle error status from API
      if (response.data?.status === 'error') {
        const errorMessage = response.data.message || 'An error occurred fetching lever data';
        throw new Error(errorMessage);
      }

      return response.data;
    } catch (err) {
      // Don't set global error state, just throw the error for individual components to handle
      if (err instanceof Error) {
        throw err;
      }

      // Convert other error types to Error objects
      if (err instanceof AxiosError) {
        if (err.response?.data?.message) {
          throw new Error(err.response.data.message);
        } else if (err.response) {
          throw new Error(`Server error (${err.response.status}): ${err.response.statusText}`);
        } else if (err.request) {
          throw new Error('No response from server. Please check if the API server is running.');
        }
      }

      throw new Error('An unknown error occurred while fetching lever data');
    }
  }

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

  async function runModel(sector?: string) {
    try {
      isLoading.value = true;
      error.value = null;

      // The API reads the string by position, so it must follow the order the
      // backend gave us (it comes from the model). Fall back to the local list
      // when the config could not be loaded.
      const modelKeys = getLeverKeys();
      const order = modelKeys.length > 0 ? modelKeys : leversData.map((l) => l.code);
      const leverValues = order.map((code) =>
        Math.round(levers.value[code] ?? getDefaultLeverValue(code)),
      );

      // Convert to string format expected by API
      const leverString = leverValues.join('');

      // Use current sector if not provided
      const sectorToRun = sector || currentSector.value || undefined;

      // Use the API service
      const response = await modelService.runModel(leverString, sectorToRun);
      console.log('Running model with lever string:', leverString, 'for sector:', sectorToRun);
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

  function isValidLeverValue(
    lever: Lever | { code: string; range: (string | number)[]; type: string },
    value: number,
  ): boolean {
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
    leverData,
    currentSector,

    // Getters with translations
    getLeverValue,
    getAllLeverValues,
    leversByHeadline,
    leversByGroup,
    getLeversForSector,
    isCustomPathway,

    getSectorDataWithKpis,

    // Pathway comparison
    pathwayComparison,
    pathwayComparisonProgress,
    pathwayComparisonLoading,
    pathwayComparisonError,
    ensurePathwayComparison,

    // Actions
    batchUpdateLevers,
    runModel,
    setLeverValue,
    applyPathway,
    resetToDefaults,
    fetchLeverData,
    setCustomPathwayName: (name: string) => {
      customPathwayName.value = name;
    },
    setCurrentSector: (sector: string | null) => {
      currentSector.value = sector;
      // Re-run model with new sector if auto-run is enabled
      if (autoRun.value) {
        debouncedRunModel();
      }
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
